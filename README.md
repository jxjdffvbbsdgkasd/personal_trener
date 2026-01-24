# Cyber Trener – System Analizy Biomechaniki Ruchu

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-green)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Pose%20Estimation-orange)
![Vosk](https://img.shields.io/badge/Vosk-Offline%20ASR-yellow)
![Pygame](https://img.shields.io/badge/Pygame-GUI-red)

**Cyber Trener** to inteligentny system wspomagający trening siłowy, działający w czasie rzeczywistym. Aplikacja wykorzystuje **stereowizję (dwie kamery)** do rekonstrukcji szkieletu w 3D, analizuje poprawność techniczną ćwiczeń i koryguje błędy użytkownika za pomocą komunikatów głosowych.

---

## Kluczowe Funkcjonalności

- **Analiza Stereowizyjna 3D:** Wykorzystanie kamery lokalnej i kamery IP (np. smartfon) do precyzyjnej oceny głębi ruchu, niemożliwej przy użyciu jednej kamery.
- **Wirtualny Trener Personalny:**
  - Automatyczne zliczanie powtórzeń.
  - Wykrywanie błędów technicznych: "Bujanie tułowiem" (Swing), "Odwodzenie łokci" (Flare), niepełny zakres ruchu.
  - Feedback głosowy (TTS) i wizualny (zmiana koloru szkieletu).
- **Sterowanie Głosem (Offline):** Pełna obsługa bezdotykowa dzięki modelowi Vosk (komendy: _Start, Stop, Reset, Biceps, Barki_).
- **Zarządzanie Treningiem:**
  - System kont użytkowników (Logowanie/Rejestracja).
  - Historia treningów i statystyki w bazie SQLite.
  - Mechanizmy dyscypliny (blokada resetu niedokończonej serii).

---

## Stack Technologiczny

Projekt oparty jest na języku **Python** i wykorzystuje architekturę wielowątkową dla zapewnienia płynności (45+ FPS) na standardowych komputerach PC.

| Komponent       | Technologia       | Opis                                                             |
| :-------------- | :---------------- | :--------------------------------------------------------------- |
| **Wizja**       | OpenCV, MediaPipe | Detekcja pozy, obsługa strumieni wideo, renderowanie szkieletu.  |
| **Audio**       | Vosk, PyAudio     | Rozpoznawanie mowy offline (ASR).                                |
| **Logika**      | NumPy             | Obliczenia wektorowe, triangulacja 3D, algorytmy biomechaniczne. |
| **GUI**         | Pygame            | Interfejs użytkownika, rysowanie panelu bocznego.                |
| **Baza Danych** | SQLite            | Przechowywanie użytkowników, sesji i ustawień.                   |

---

## Instalacja i Konfiguracja

Model rozpoznawania mowy został już dołączony do repozytorium, w celu ułatwienia instalacji.

### 1. Klonowanie repozytorium

```bash
git clone https://github.com/jxjdffvbbsdgkasd/personal_trener.git
cd CyberTrener
```

### 2. Instalacja zależności

Zalecane jest użycie wirtualnego środowiska (venv).

```bash
python -m venv venv
```

#### W zależności od systemu:

- **Windows:**

```bash
venv\Scripts\activate
```

(Jeśli używasz PowerShell i napotkasz błąd uprawnień, spróbuj:)

```bash
Set-ExecutionPolicy Unrestricted -Scope Process
```

lub użyj cmd

- **macOS / Linux:**

```bash
source venv/bin/activate
```

### Gdy widzisz (venv) przed ścieżka:

```bash
pip install -r requirements.txt
```

### 3. Konfiguracja Kamery IP

Aby skorzystać z drugiej kamery (np. telefon) dla pełnej analizy 3D:

1. Zainstaluj aplikację typu IP Webcam na telefonie i uruchom serwer.
2. Otwórz plik settings.py i podmień adres IP w zmiennej ip_url:

```python
ip_url = "http://192.168.X.X:YYYY/video"
```

## Obsługa aplikacji

Poprawne ustawienie kamer jest kluczowe do poprawnego działania aplikacji.

1. **Ustawienie:** Kamery powinny stworzyć literę "V" skierowaną na ćwiczącego.
   - **Kamera 1 (Laptop):** Ustawiona pod kątem ok. 45 stopni z lewej strony.
   - **Kamera 2 (Telefon)** Ustawiona pod kątem ok. 45 stopni z prawej strony.
2. **Logowanie:** Utwórz konto lub zaloguj się.
3. **Menu:** Kliknij "Rozpocznij Trening".
4. **Komendy głosowe:**
   - "Biceps" / "Barki" - Wybór ćwiczenia.
   - "Start" - Rozpoczęcie analizy i zliczania.
   - "Stop" - Zakończenie serii i zapis do bazy.
   - "Reset" - Wyzerowanie liczników.

## Uruchomienie

Aby włączyć aplikację, wpisz w terminalu:

```bash
python main.py
```

## Autorzy

Projekt realizowany w ramach przedmiotu **Przetwarzanie sygnałów i obrazów** na **Politechnice Łódzkiej.**

- Filip Mateusiak
- Filip Piliszek
- Michał Wiśniewski
- Mateusz Oczkiewicz
