import streamlit as st
import requests
import pandas as pd
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

st.set_page_config(page_title="Website-Check", page_icon="❄️", layout="wide")

st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #eef7ff 0%, #ffffff 45%, #f5fbff 100%); }
.hero { padding: 35px; border-radius: 24px; background: white; box-shadow: 0 12px 35px rgba(0,0,0,0.08); margin-bottom: 25px; }
.hero h1 { font-size: 46px; margin-bottom: 10px; }
.hero p { font-size: 18px; color: #52677a; }
.card { padding: 24px; border-radius: 22px; background: white; box-shadow: 0 10px 28px rgba(0,0,0,0.08); border: 1px solid #e5eef7; }
.score { font-size: 44px; font-weight: 800; }
.good { color: #16a34a; }
.mid { color: #ca8a04; }
.bad { color: #dc2626; }
.quickwin { padding: 14px 16px; border-radius: 14px; background: #f0f9ff; border-left: 6px solid #38bdf8; margin-bottom: 12px; }
.cta { padding: 28px; border-radius: 22px; background: #0f172a; color: white; margin-top: 25px; }
.cta-button { display:inline-block; margin-top:14px; padding:14px 22px; border-radius:12px; background:#38bdf8; color:#0f172a !important; text-decoration:none; font-weight:800; }
.snippet { background: white; padding: 18px; border-radius: 16px; border: 1px solid #dbeafe; }
.snippet-title { color: #1a0dab; font-size: 20px; }
.snippet-url { color: #006621; font-size: 14px; }
.snippet-desc { color: #4d5156; font-size: 15px; }
.notice { color: #64748b; font-size: 14px; margin-top: 6px; }
</style>
""", unsafe_allow_html=True)


def normalize_url(url):
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")


def valid_email(email):
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return re.match(pattern, email) is not None


def get_html(url):
    headers = {"User-Agent": "Mozilla/5.0 Website Check"}
    start = time.time()
    response = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
    load_time = round(time.time() - start, 2)
    return response.text, response.status_code, load_time, response.url


def score_color(score):
    if score >= 80:
        return "good"
    if score >= 55:
        return "mid"
    return "bad"


def analyse_website(url):
    html, status_code, load_time, final_url = get_html(url)
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True).lower()

    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    meta = soup.find("meta", attrs={"name": "description"})
    description = meta.get("content", "").strip() if meta and meta.get("content") else ""

    h1 = soup.find_all("h1")
    h2 = soup.find_all("h2")
    images = soup.find_all("img")
    images_without_alt = [img.get("src") for img in images if not img.get("alt")]

    viewport = soup.find("meta", attrs={"name": "viewport"})
    schema = soup.find_all("script", type="application/ld+json")

    email_found = bool(re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text))
    phone_found = bool(re.search(r"(\+?\d[\d\s\/()-]{7,}\d)", text))
    address_found = bool(re.search(r"\b\d{5}\b", text)) or "straße" in text or "strasse" in text
    maps_found = "google.com/maps" in html.lower() or "maps.app.goo.gl" in html.lower()
    faq_found = "faq" in text or "häufige fragen" in text

    links = []
    for a in soup.find_all("a", href=True):
        full = urljoin(final_url, a.get("href"))
        if full.startswith(("http://", "https://")):
            links.append(full)

    seo_score = 100
    ki_score = 100
    local_score = 100
    quickwins = []

    if status_code != 200:
        seo_score -= 20
        quickwins.append("Die Website-Erreichbarkeit prüfen.")

    if not title:
        seo_score -= 15
        quickwins.append("Einen klaren SEO-Titel ergänzen.")
    elif len(title) < 35:
        seo_score -= 10
        quickwins.append("SEO-Titel erweitern und Hauptleistung + Ort ergänzen.")

    if not description:
        seo_score -= 15
        quickwins.append("Meta Description ergänzen.")
    elif len(description) < 80:
        seo_score -= 8
        quickwins.append("Meta Description verkaufsstärker formulieren.")

    if len(h1) != 1:
        seo_score -= 10
        quickwins.append("Eine klare H1-Hauptüberschrift definieren.")

    if len(images_without_alt) > 0:
        seo_score -= min(15, len(images_without_alt) * 2)
        quickwins.append("ALT-Texte für Bilder ergänzen.")

    if load_time > 3:
        seo_score -= 10
        quickwins.append("Ladezeit der Website verbessern.")

    if not viewport:
        seo_score -= 8
        quickwins.append("Mobile Darstellung prüfen.")

    if not schema:
        ki_score -= 25
        quickwins.append("Strukturierte Daten / Schema Markup ergänzen.")

    if not faq_found:
        ki_score -= 20
        quickwins.append("FAQ-Bereich für bessere KI-Sichtbarkeit ergänzen.")

    if len(h2) < 2:
        ki_score -= 10
        quickwins.append("Mehr klare Zwischenüberschriften einbauen.")

    if len(text.split()) < 500:
        ki_score -= 15
        quickwins.append("Mehr erklärenden Inhalt auf der Seite ergänzen.")

    if not phone_found:
        local_score -= 20
        quickwins.append("Telefonnummer sichtbarer platzieren.")

    if not email_found:
        local_score -= 15
        quickwins.append("E-Mail-Adresse besser sichtbar machen.")

    if not address_found:
        local_score -= 20
        quickwins.append("Adresse / Standort klarer darstellen.")

    if not maps_found:
        local_score -= 15
        quickwins.append("Google Maps oder Standort-Verlinkung einbauen.")

    if not schema:
        local_score -= 15

    seo_score = max(seo_score, 0)
    ki_score = max(ki_score, 0)
    local_score = max(local_score, 0)

    lead_score = round((100 - seo_score) * 0.35 + (100 - local_score) * 0.45 + (100 - ki_score) * 0.2 + 50)
    lead_score = min(max(lead_score, 0), 100)

    return {
        "Final URL": final_url,
        "Status Code": status_code,
        "Ladezeit": load_time,
        "Title": title,
        "Title Länge": len(title),
        "Meta Description": description,
        "Description Länge": len(description),
        "H1 Anzahl": len(h1),
        "H2 Anzahl": len(h2),
        "Bilder gesamt": len(images),
        "Bilder ohne ALT": len(images_without_alt),
        "Links": len(set(links)),
        "E-Mail sichtbar": "Ja" if email_found else "Nein",
        "Telefon sichtbar": "Ja" if phone_found else "Nein",
        "Adresse erkannt": "Ja" if address_found else "Nein",
        "Google Maps erkannt": "Ja" if maps_found else "Nein",
        "FAQ erkannt": "Ja" if faq_found else "Nein",
        "Schema erkannt": "Ja" if schema else "Nein",
        "SEO Score": seo_score,
        "KI Score": ki_score,
        "Local Score": local_score,
        "Lead Potenzial": lead_score,
        "Quickwins": list(dict.fromkeys(quickwins))[:6],
    }


st.markdown("""
<div class="hero">
<h1>🚀 Kostenloser Website-Check</h1>
<p>Tragen Sie Ihre Website ein und erhalten Sie eine erste Einschätzung zu Google-Sichtbarkeit, lokaler Auffindbarkeit und KI-Lesbarkeit.</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    email = st.text_input("📧 E-Mail-Adresse *", placeholder="max@firma.de")

with col2:
    website = st.text_input("🌐 Ihre Website *", placeholder="https://www.ihre-webseite.de")

st.markdown('<div class="notice">* Pflichtfeld. Die Website wird erst nach Eingabe einer gültigen E-Mail-Adresse geprüft.</div>', unsafe_allow_html=True)

start = st.button("Website kostenlos prüfen", use_container_width=True)

if start:
    if not email:
        st.warning("Bitte E-Mail-Adresse eingeben.")
        st.stop()

    if not valid_email(email):
        st.warning("Bitte eine gültige E-Mail-Adresse eingeben.")
        st.stop()

    if not website:
        st.warning("Bitte Website eintragen.")
        st.stop()

    try:
        url = normalize_url(website)

        with st.spinner("Website wird analysiert..."):
            result = analyse_website(url)

        st.markdown("## Ihr Ergebnis")

        c1, c2, c3, c4 = st.columns(4)

        for col, label, key, sub in [
            (c1, "SEO Score", "SEO Score", "Google-Basis"),
            (c2, "KI-Sichtbarkeit", "KI Score", "ChatGPT & Co."),
            (c3, "Local SEO", "Local Score", "Lokale Anfragen"),
            (c4, "Anfrage-Potenzial", "Lead Potenzial", "Mehr Kundenkontakte"),
        ]:
            with col:
                st.markdown(f"""
                <div class="card">
                <div>{label}</div>
                <div class="score {score_color(result[key])}">{result[key]}/100</div>
                <small>{sub}</small>
                </div>
                """, unsafe_allow_html=True)
                st.progress(result[key] / 100)

        st.markdown("## Google-Vorschau")

        st.markdown(f"""
        <div class="snippet">
            <div class="snippet-title">{result['Title'] or 'Kein Seitentitel vorhanden'}</div>
            <div class="snippet-url">{result['Final URL']}</div>
            <div class="snippet-desc">{result['Meta Description'] or 'Keine Meta Description vorhanden'}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("## Top Quick Wins")

        if result["Quickwins"]:
            for win in result["Quickwins"]:
                st.markdown(f'<div class="quickwin">✅ {win}</div>', unsafe_allow_html=True)
        else:
            st.success("Keine offensichtlichen Schwachstellen gefunden.")

        st.markdown("""
        <div class="cta">
        <h2>🎯 Kostenlose Erstberatung sichern</h2>
        <p>Wir zeigen Ihnen, welche Punkte sich am schnellsten verbessern lassen und wie daraus mehr Anfragen entstehen können.</p>
        <a class="cta-button" href="tel:+491742769796">📞 Jetzt anrufen: 0174 2769796</a>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("Technische Details anzeigen"):
            details = {k: v for k, v in result.items() if k != "Quickwins"}
            st.dataframe(pd.DataFrame([details]), use_container_width=True)

        csv = pd.DataFrame([{k: v for k, v in result.items() if k != "Quickwins"}]).to_csv(index=False).encode("utf-8-sig")
        st.download_button("Analyse als CSV herunterladen", csv, "website_check.csv", "text/csv")

    except Exception as e:
        st.error(f"Fehler: {e}")