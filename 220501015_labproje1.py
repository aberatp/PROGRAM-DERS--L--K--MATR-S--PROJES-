import pandas as pd
import requests
from bs4 import BeautifulSoup


# Web sayfasından öğrenim çıktıları çekme
def fetch_learning_outcomes():
    url = "https://ebs.kocaelisaglik.edu.tr/Pages/LearningOutcomesOfProgram.aspx?lang=tr-TR&academicYear=2024&facultyId=5&programId=1&menuType=course&catalogId=2227"
    response = requests.get(url, timeout=10)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # Öğrenim çıktıları satırlarını seç
        rows = soup.find_all('tr',
                             {'id': lambda x: x and x.startswith('Content_Content_grid_LearningOutComes_DXDataRow')})

        learning_outcomes = []
        if rows:
            for row in rows:
                columns = row.find_all('td')
                if len(columns) >= 2:  # En az iki sütun olduğundan emin olun
                    outcome = columns[1].get_text(strip=True)  # Öğrenim çıktısı
                    learning_outcomes.append(outcome)
        else:
            print("Öğrenim çıktıları bulunamadı.")
        return learning_outcomes
    else:
        print(f"Sayfa alınamadı. HTTP Durum Kodu: {response.status_code}")
        return []


# Kullanıcıdan TABLO 1 girdisi alma (Program Çıktıları ve Ders Çıktıları İlişki Matrisi)
def get_table1(learning_outcomes):
    print("TABLO 1: Program çıktıları ve ders çıktıları ilişki matrisi (0, 1 veya float değerleri girin):")
    rows = int(input("Program çıktısı (Prg Çıktı) sayısını girin: "))
    cols = len(learning_outcomes)  # Web'den alınan öğrenim çıktısı sayısı
    data = []

    for i in range(rows):
        row = input(f"Prg Çıktı {i + 1} için {cols} değer (0, 1 veya float, boşlukla ayırın): ").split()
        row = [float(x) for x in row]
        toplam = sum(row)
        ilişki_değeri = toplam / cols if cols > 0 else 0
        row.append(round(ilişki_değeri, 2))  # İlişki Değ. sütununu ekle
        data.append(row)

    # Sütun başlıklarını oluştur
    columns = [f"Ders Çıktı {i + 1}" for i in range(cols)] + ["İlişki Değ."]
    df_table1 = pd.DataFrame(data, columns=columns)
    df_table1.index = [f"Prg Çıktı {i + 1}" for i in range(rows)]

    # Öğrenim çıktıları metinlerini ekleme
    df_table1["Ders Çıktıları"] = learning_outcomes
    return df_table1


# Kullanıcıdan TABLO 2 girdisi alma
def get_table2():
    print("TABLO 2: Değerlendirme kriterlerini, ağırlık yüzdelerini ve ders çıktıları değerlerini girin:")
    criteria = ["Öd1", "Öd2", "Quiz", "Vize", "Fin"]
    ders_cikti = int(input("Ders çıktısı sayısını girin: "))
    weights = []
    data = []

    # Ağırlıkları al
    for criterion in criteria:
        weight = float(input(f"{criterion} için ağırlık girin (%): "))
        if weight > 100:  # Eğer ağırlık 100'ü geçerse uyarı ver
            print(f"{criterion} ağırlığı 100'ü geçemez!")
            weight = 100  # Burada 100 olarak sınırlıyoruz
        weights.append(weight)

    # Ders çıktıları için 0 ve 1 değerlerini al
    for i in range(ders_cikti):
        row = input(
            f"Ders çıktısı {i + 1} için Öd1, Öd2, Quiz, Vize, Fin değerlerini girin (0 veya 1, boşlukla ayırın): ").split()
        row = [int(x) for x in row]
        row.append(sum(row))  # Toplam sütunu ekle
        data.append(row)

    # TABLO 2'nin DataFrame'i
    df_table2 = pd.DataFrame(data, columns=criteria + ["TOPLAM"])
    df_table2.loc["Ağırlıklar"] = weights + [""]  # Ağırlıkları ekle
    return df_table2, weights


# TABLO 3: Ağırlıklı değerlendirme tablosunu hesaplama
def calculate_weighted_table(weights, ders_cikti):
    print("TABLO 3: Ağırlıklı değerlendirme tablosu hazırlanıyor...")
    criteria = ["Öd1", "Öd2", "Quiz", "Vize", "Fin"]
    weighted_data = []

    # Her ders çıktısı için ağırlıklı puanları hesapla
    for i in range(ders_cikti):
        weighted_row = {criteria[j]: weights[j] for j in range(len(criteria))}
        weighted_row["TOPLAM"] = sum(weighted_row[criteria[j]] for j in range(len(criteria)))
        weighted_data.append(weighted_row)

    table3 = pd.DataFrame(weighted_data)
    return table3


# Kullanıcıdan öğrenci notlarını alma (TABLO NOT)
def get_student_scores():
    print("TABLO NOTLAR: Öğrenci notlarını girin:")
    student_scores = {}
    num_students = int(input("Kaç öğrenci için not girmek istiyorsunuz? "))
    for _ in range(num_students):
        student_name = input("Öğrencinin adı: ")
        scores = input("Öğrencinin sırasıyla Öd1, Öd2, Quiz, Vize, Fin notlarını girin (boşlukla ayırın): ").split()
        student_scores[student_name] = [float(score) for score in scores]
    return student_scores


# TABLO 4 ve TABLO 5: Öğrenci başarı oranlarını hesaplama
def calculate_student_tables(table1, student_scores, weights):
    tables = {}
    num_program_outcomes = len(table1)

    for student, scores in student_scores.items():
        # TABLO 4
        table4 = pd.DataFrame({
            "Ders Çıktı": range(1, len(table1.columns)),
            "Öd1": [scores[0] * weights[0]] * len(table1.columns[:-1]),
            "Öd2": [scores[1] * weights[1]] * len(table1.columns[:-1]),
            "Quiz": [scores[2] * weights[2]] * len(table1.columns[:-1]),
            "Vize": [scores[3] * weights[3]] * len(table1.columns[:-1]),
            "Fin": [scores[4] * weights[4]] * len(table1.columns[:-1]),
        })
        table4["TOPLAM"] = table4.iloc[:, 1:].sum(axis=1)
        table4["MAX"] = 100 * sum(weights)  # Maksimum ağırlıklı değer
        table4["% Başarı"] = table4["TOPLAM"] / table4["MAX"] * 100
        tables[f"TABLO 4 - {student}"] = table4

        # TABLO 5
        table5 = pd.DataFrame({
            "Prg Çıktı": range(1, num_program_outcomes + 1),
            "% Başarı": [table4["% Başarı"].mean()] * num_program_outcomes  # Ortalama başarı oranı
        })
        tables[f"TABLO 5 - {student}"] = table5

    return tables


# Excel dosyasını oluşturma
def generate_excel_file(table1, table2, table3, student_tables):
    file_path = "output.xlsx"
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        # TABLO 1
        table1.to_excel(writer, sheet_name='TABLO 1', index=True)

        # TABLO 2
        table2.to_excel(writer, sheet_name='TABLO 2', index=False)

        # TABLO 3
        table3.to_excel(writer, sheet_name='TABLO 3', index=False)

        # TABLO 4 ve TABLO 5 (Her öğrenci için)
        for sheet_name, table in student_tables.items():
            table.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"Excel dosyası '{file_path}' olarak oluşturuldu.")


# Program akışı
if __name__ == "__main__":
    learning_outcomes = fetch_learning_outcomes()  # Web'den öğrenim çıktıları alın
    table1 = get_table1(learning_outcomes)  # TABLO 1
    table2, weights = get_table2()  # TABLO 2
    ders_cikti = len(table2) - 1  # Ders çıktısı sayısı (ağırlıklar hariç)
    table3 = calculate_weighted_table(weights, ders_cikti)  # TABLO 3
    student_scores = get_student_scores()  # Öğrenci notları
    student_tables = calculate_student_tables(table1, student_scores, weights)  # TABLO 4 ve 5
    generate_excel_file(table1, table2, table3, student_tables)  # Excel dosyasını oluştur
