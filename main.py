from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from get_class import get_class
import os

app = Flask(__name__)
app.secret_key = 'fa7b0c9416d3eab2c4f80b2197daeeaf'  # session için zorunlu

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diary.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Upload folder konfigürasyonu
UPLOAD_FOLDER = os.path.join('static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# AI Model konfigürasyonu
MODEL_PATH = "keras_model.h5"
LABELS_PATH = "labels.txt"

siniflar = {
    "Enerji Tasarrufu": (
        "Elektrik, doğalgaz ve yakıt gibi kaynakların gereksiz kullanımını azaltarak çevreyi korumaya katkı sağlar. "
        "Enerji tasarrufu sayesinde fatura maliyetleri düşer. "
        "Doğal kaynakların daha uzun süre kullanılmasına yardımcı olur. "
        "Basit alışkanlıklar değişikliğiyle büyük ölçekte fayda sağlanabilir."
    ),
    "Yenilenebilir Enerji": (
        "Yenilenebilir enerji, kendini sürekli yenileyebilen doğal kaynaklardan elde edilir. "
        "Güneş, rüzgar, hidroelektrik, jeotermal ve biyokütle bu kaynaklara örnektir. "
        "Fosil yakıtlara kıyasla çok daha temizdir ve çevre kirliliğini azaltır. "
        "Sürdürülebilir bir gelecek için yenilenebilir enerjiye geçiş büyük önem taşır."
    ),
    "Toplu Taşıma Yerine Bisiklet Kullanmak": (
        "Bisiklet kullanmak, karbon salınımını azaltarak çevreye dost bir ulaşım yöntemidir. "
        "Trafik yoğunluğunu hafifletir ve zaman kazandırır. "
        "Düzenli bisiklet sürmek, kalp ve damar sağlığına olumlu katkılar sağlar. "
        "Şehirlerde bisiklet yollarının yaygınlaşması bu alışkanlığı teşvik eder."
    ),
    "Ağaç Dikmek": (
        "Ağaçlar karbondioksiti emerek oksijen üretir ve hava kalitesini artırır. "
        "Toprak erozyonunu önleyerek doğal dengeyi korur. "
        "Kuşlar, böcekler ve birçok canlı için yaşam alanı sağlar. "
        "Her dikilen ağaç, gelecek nesiller için değerli bir mirastır."
    ),
    "Geri Dönüşüm": (
        "Geri dönüşüm, atık malzemelerin işlenerek yeniden kullanılmasıdır. "
        "Kağıt, plastik, cam ve metal gibi maddeler geri dönüştürülebilir. "
        "Doğal kaynakların korunmasını sağlar ve çevre kirliliğini azaltır. "
        "Bireysel olarak geri dönüşüme katılmak, büyük ölçekte fark yaratır."
    ),
    "Su Tasarrufu": (
        "Su tasarrufu, mevcut su kaynaklarını bilinçli şekilde kullanmayı ifade eder. "
        "Muslukları gereksiz yere açık bırakmamak en temel yöntemdir. "
        "Tarımda damla sulama gibi verimli yöntemler büyük ölçekte su tasarrufu sağlar. "
        "Su kaynaklarının korunması, iklim değişikliğine karşı alınacak önlemlerin başında gelir."
    ),
    "Yerel ve Mevsimlik Ürünler": (
        "Yerel ürünler, yakın çevrede yetiştirilen tarım ürünleridir. "
        "Mevsimlik ürünleri tüketmek daha sağlıklıdır ve doğallığı artırır. "
        "Ulaşım kaynaklı karbon salınımını azaltarak çevreye katkı sağlar. "
        "Aynı zamanda yerel üreticilerin desteklenmesine yardımcı olur."
    ),
    
    "Deprem": (
        "Deprem, yer kabuğundaki fay hatlarının kırılması sonucu meydana gelir. "
        "Şiddetine göre can ve mal kayıplarına yol açabilir. "
        "Depreme dayanıklı yapılar inşa etmek büyük önem taşır. "
        "Acil durum çantası ve deprem tatbikatları hayati kurtarıcı olabilir."
    ),
    "Sel": (
        "Sel, aşırı yağış, taşkın veya eriyen karların su baskınına yol açmasıdır. "
        "Tarım alanlarına, altyapıya ve evlere büyük zarar verir. "
        "Şehirlerde sel riskini azaltmak için yağmur suyu kanalları geliştirilmelidir. "
        "Erken uyarı sistemleri ve planlı şehirleşme sel felaketlerinin etkisini azaltır."
    ),
    "Heyelan": (
        "Heyelan, yerçekimi etkisiyle toprak ve kaya kütlelerinin yamaçtan kaymasıdır. "
        "Çok sayıda can ve mal kaybına yol açabilir. "
        "Ormanların korunması heyelan riskini azaltır. "
        "Tehlike bölgelerinde yapılaşmadan kaçınmak en önemli önlemdir."
    ),
    "Çığ": (
        "Çığ, kar yığınlarının yamaçtan aşağı hızla kaymasıdır. "
        "Dağlık ve karlı bölgelerde ciddi tehlike oluşturur. "
        "Dağcılar için uyarı sistemleri ve güvenlik ekipmanları hayati önem taşır. "
        "Ormancılık ve uygun arazi kullanımı çığ riskini azaltabilir."
    ),
    "Volkan Patlaması": (
        "Volkan patlamaları, yer altındaki magmanın basınçla yüzeye çıkmasıdır. "
        "Kül, lav ve gazlar çevreye yayılır. "
        "Çevresindeki yerleşim yerlerinde büyük yıkımlara neden olabilir. "
        "Sismik gözlemler ve uyarı sistemleriyle önceden tedbir almak mümkündür."
    ),
    "Kuraklık": (
        "Kuraklık, uzun süre yağış olmaması sonucu ortaya çıkar. "
        "Su kaynakları azalır ve tarımsal üretim olumsuz etkilenir. "
        "İklim değişikliğinin etkisiyle kuraklıklar daha sık görülmektedir. "
        "Su tasarrufu ve sürdürülebilir tarım kuraklığa karşı alınabilecek önlemlerdir."
    ),
    "Tsunami": (
        "Tsunami, deniz altı depremleri veya volkanik patlamalar sonucu oluşur. "
        "Büyük dalgalar kıyı bölgelerinde büyük yıkıma yol açar. "
        "Erken uyarı sistemleri binlerce hayatı kurtarabilir. "
        "Kıyı bölgelerinde güvenli tahliye planları hazırlanmalıdır."
    ),
    "Yangın": (
        "Yangın, kontrolsüz şekilde yayılan ateştir. "
        "Orman yangınları ekosisteme ve canlılara ciddi zararlar verir. "
        "İnsan kaynaklı dikkatsizlik yangınların en büyük sebeplerindendir. "
        "Yangın söndürme ekipmanlarının hazır olması hayati önemdedir."
    ),
    "Hortum": (
        "Hortum, şiddetli fırtınalarda oluşan dönerek hareket eden hava sütunudur. "
        "Çok kısa sürede büyük yıkımlar yapabilir. "
        "Hortum sırasında kapalı ve güvenli alanlarda kalmak gerekir. "
        "Meteorolojik takip ve erken uyarılar hortumun zararını azaltır."
    )
}

@app.route('/cevre_analiz', methods=['GET', 'POST'])
def cevre_analiz():
    prediction = None
    description = None
    error = None
    image_url = None

    if request.method == 'POST':
        if 'image' not in request.files:
            error = "Dosya yüklenmedi!"
            return render_template('cevre_analiz.html', error=error)

        file = request.files['image']
        if file.filename == '':
            error = "Dosya seçilmedi!"
            return render_template('cevre_analiz.html', error=error)

        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Session'a kaydet
            session['uploaded_image'] = filename

            image_url = url_for('static', filename=f'uploads/{filename}')

            try:
                # get_class fonksiyonunu kullanarak tahmin yap
                prediction = get_class(MODEL_PATH, LABELS_PATH, filepath)
                
                if prediction is None:
                    error = "Görsel analiz edilemedi."
                else:
                    # Tahmin için açıklama al
                    description = siniflar.get(prediction, "Bu görsel çevre ile ilgili bir konuyu gösteriyor. Daha detaylı analiz için uzman görüşü alınabilir.")
            except Exception as e:
                error = f"Görsel analiz edilirken hata: {e}"
    
    # GET request veya POST request sonrası template'i render et
    return render_template('cevre_analiz.html', 
                         prediction=prediction, 
                         description=description, 
                         error=error, 
                         image_url=image_url)
@app.route('/')
def home():
    # Yüklü resim varsa sil
    filename = session.pop('uploaded_image', None)
    if filename:
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(path):
            os.remove(path)

    user_email = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            user_email = user.login
    return render_template('index.html', user_email=user_email)

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    subtitle = db.Column(db.String(300), nullable=False)
    text = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    login = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(30), nullable=False)
    cards = db.relationship('Card', backref='user', lazy=True)
    
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.String(50), nullable=False)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    next_page = request.args.get('next')

    if request.method == 'POST':
        form_login = request.form['email']
        form_password = request.form['password']
        next_page = request.form.get('next')

        user = User.query.filter_by(login=form_login, password=form_password).first()
        if user:
            session['user_id'] = user.id
            # Eğer next yoksa veya boşsa direkt home'a at
            return redirect(next_page if next_page else url_for('home'))
        else:
            error = 'Hatalı giriş veya şifre'
    
    return render_template('login.html', error=error, next=next_page)

@app.route('/reg', methods=['GET', 'POST'])
def reg():
    if request.method == 'POST':
        login = request.form['email']
        password = request.form['password']

        user = User(login=login, password=password)
        db.session.add(user)
        db.session.commit()

        return redirect('/login')
    else:
        return render_template('registration.html')
    
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    error = ''
    success = ''

    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['new_password']

        user = User.query.filter_by(login=email).first()

        if user:
            user.password = new_password
            db.session.commit()
            success = 'Şifreniz başarıyla güncellendi. Giriş yapabilirsiniz.'
        else:
            error = 'Bu e-posta adresiyle kayıtlı bir kullanıcı bulunamadı.'

    return render_template('forgot_password.html', error=error, success=success)

@app.route('/hakkinda')
def hakkinda():
    return render_template('hakkinda.html')

@app.route('/dogal_afet')
def dogal_afet():
    return render_template('dogal_afet.html')

@app.route('/filmler')
def filmler():
    return render_template('filmler.html')

@app.route('/iklim_degisikligi')
def iklim_degisikligi():
    return render_template('iklim_degisikligi.html')

@app.route('/discord')
def discord():
    return redirect("https://discord.gg/pEU8uxVU")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
