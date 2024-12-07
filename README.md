
# **README - Proiect IoT: Monitorizarea Temperaturii**

## **Descriere**
Acest proiect reprezinta un sistem IoT dezvoltat in mediul de simulare Wokwi, care permite monitorizarea temperaturii pentru o locatie specificata. Utilizatorul selecteaza coordonatele geografice (latitudine si longitudine) printr-o aplicatie web cu o harta interactiva, iar un server ESP32 simulat returneaza temperatura curenta din locatie, utilizand API-ul Open Meteo.

Proiectul este dezvoltat pentru a functiona exclusiv in simulare, dar poate fi extins pentru a include senzori si actuatori fizici.

---

## **Cerinte**
Pentru a rula proiectul, sunt necesare urmatoarele:
- **Wokwi Simulator** (pentru rularea serverului ESP32)
- **Python 3.x** (pentru rularea serverului HTTP local)
- **Browser modern** (Google Chrome, Mozilla Firefox, Microsoft Edge)
- Conexiune la internet (pentru accesarea API-ului Open Meteo)

---

## **Instalare si rulare**

### **1. Configurarea serverului ESP32 in Wokwi**
1. Acceseaza platforma Wokwi la [https://wokwi.com/](https://wokwi.com/).
2. Creeaza un nou proiect ESP32.
3. Copiaza si lipeste codul din fisierul `temperature.py` in editorul de cod al simulatorului.
4. Porneste simularea in Wokwi.
5. Verifica in consola simulatorului ca serverul ruleaza si afiseaza mesajul:
   ```
   Server running on http://localhost:9080
   ```

---

### **2. Configurarea aplicatiei web**
1. Creeaza un director local pe computer pentru proiect si plaseaza fisierul `webapp.html` in acesta.
2. Deschide un terminal in directorul respectiv si ruleaza un server HTTP local utilizand Python:
   ```bash
   python3 -m http.server
   ```
3. Acceseaza aplicatia web in browser, la adresa:
   ```
   http://localhost:8000/webapp.html
   ```

---

### **3. Rularea proiectului**
1. In aplicatia web:
   - Introdu manual coordonatele geografice (latitudine si longitudine) **sau** selecteaza o locatie direct pe harta interactiva.
   - Apasa butonul **Get Temperature** pentru a trimite o cerere catre serverul ESP32.
2. Verifica rezultatul afisat in aplicatia web. Daca serverul functioneaza corect, temperatura curenta pentru locatia specificata va fi afisata:
   ```
   Temperature: 25.5°C
   ```
3. In caz de erori, verifica consola simulatorului Wokwi pentru a vedea logurile serverului.

---

## **Structura proiectului**
- `temperature.py`: Codul serverului ESP32 care ruleaza in Wokwi.
- `webapp.html`: Aplicatia web care permite utilizatorilor sa trimita cereri catre serverul ESP32.
- `README.md`: Documentatia proiectului.

---

## **Depanare**
1. **Probleme de conexiune:**
   - Asigura-te ca serverul ESP32 ruleaza si afiseaza adresa `http://localhost:9080`.
   - Verifica firewall-ul sau setarile proxy care ar putea bloca conexiunile locale.

2. **Eroare CORS:**
   - Asigura-te ca serverul ESP32 include header-ul `Access-Control-Allow-Origin: *` in raspunsuri.

3. **Cereri lente sau esuate:**
   - Verifica conexiunea la internet.
   - Creste timeout-ul in codul aplicatiei web daca raspunsurile de la API-ul Open Meteo sunt intarziate.

---

## **Licenta**
Acest proiect este disponibil sub licenta open-source si poate fi utilizat, modificat sau distribuit conform termenilor aplicabili.
