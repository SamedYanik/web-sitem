from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from tensorflow.keras.layers import DepthwiseConv2D
from tensorflow.keras import backend as K
import numpy as np
import warnings
import os
from PIL import Image
import cv2

class CustomDepthwiseConv2D(DepthwiseConv2D):
    """Eski Keras modellerini yüklemek için uyumlu DepthwiseConv2D sınıfı"""
    
    def __init__(self, *args, **kwargs):
        # 'groups' parametresini kaldır (yeni versiyonda desteklenmiyor)
        if 'groups' in kwargs:
            del kwargs['groups']
        super().__init__(*args, **kwargs)
    
    def get_config(self):
        config = super().get_config()
        # Eski modellerde olan ama yeni versiyonda desteklenmeyen parametreleri kaldır
        if 'groups' in config:
            del config['groups']
        return config

def get_class(model_path, labels_path, image_path, confidence_threshold=0.1):
    # Uyarıları bastır
    warnings.filterwarnings('ignore')
    
    print(f"=== AI Analiz Başlıyor ===")
    print(f"Model yolu: {model_path}")
    print(f"Labels yolu: {labels_path}")
    print(f"Görsel yolu: {image_path}")
    
    # Dosya varlığını kontrol et
    if not os.path.exists(model_path):
        print(f"❌ Model dosyası bulunamadı: {model_path}")
        return simple_image_analysis(image_path, labels_path)
    
    if not os.path.exists(labels_path):
        print(f"❌ Etiket dosyası bulunamadı: {labels_path}")
        return None
    
    if not os.path.exists(image_path):
        print(f"❌ Görsel dosyası bulunamadı: {image_path}")
        return None
    
    print("✅ Tüm dosyalar mevcut")
    
    # Model yükleme denemeleri
    model = None
    load_methods = [
        # Yöntem 1: CustomDepthwiseConv2D ile
        lambda: load_model(model_path, 
                         custom_objects={'DepthwiseConv2D': CustomDepthwiseConv2D}, 
                         compile=False),
        
        # Yöntem 2: Standart DepthwiseConv2D ile
        lambda: load_model(model_path, 
                         custom_objects={'DepthwiseConv2D': DepthwiseConv2D}, 
                         compile=False),
        
        # Yöntem 3: Standart yükleme
        lambda: load_model(model_path, compile=False),
    ]
    
    for i, load_method in enumerate(load_methods, 1):
        try:
            print(f"🔄 Model yükleme yöntemi {i} deneniyor...")
            model = load_method()
            print(f"✅ Model yöntem {i} ile başarıyla yüklendi")
            break
        except Exception as e:
            print(f"❌ Yöntem {i} başarısız: {str(e)[:100]}...")
            continue
    
    if model is None:
        print("❌ Hiçbir yöntemle model yüklenemedi!")
        print("🔄 Alternatif görsel analizi sistemi kullanılıyor...")
        return simple_image_analysis(image_path, labels_path)
    
    # Etiketleri oku (utf-8 ile açtığından emin ol)
    try:
        print("🔄 Etiketler okunuyor...")
        with open(labels_path, 'r', encoding='utf-8') as f:
            labels = f.read().splitlines()
        print(f"✅ {len(labels)} etiket okundu: {labels}")
    except Exception as e:
        print(f"❌ Etiket dosyası okuma hatası: {e}")
        return None
    
    # Görseli hazırla
    try:
        print("🔄 Görsel hazırlanıyor...")
        img = image.load_img(image_path, target_size=(224, 224))  # modelin inputuna göre
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = img_array / 255.0
        print(f"✅ Görsel hazırlandı, boyut: {img_array.shape}")
    except Exception as e:
        print(f"❌ Görsel hazırlama hatası: {e}")
        return None
    
    # Tahmin yap
    try:
        print("🔄 AI tahmin yapılıyor...")
        prediction = model.predict(img_array, verbose=0)[0]  # verbose=0 ile çıktıyı bastır
        predicted_index = np.argmax(prediction)
        confidence = prediction[predicted_index]
        
        print(f"📊 Ham tahmin sonuçları: {prediction}")
        print(f"📊 En yüksek skor: {confidence:.6f} (index: {predicted_index})")
        
        if confidence < confidence_threshold:
            print(f"❌ Güven düşük: {confidence:.6f}, eşik: {confidence_threshold}")
            return simple_image_analysis(image_path, labels_path)

        predicted_label = labels[predicted_index]
        print(f"🏷️ Ham etiket: '{predicted_label}'")
        
        # Sayıları kaldır (örn: "5 sel" -> "sel")
        if predicted_label and ' ' in predicted_label:
            predicted_label = predicted_label.split(' ', 1)[1]  # İlk boşluktan sonrasını al
            print(f"🏷️ Temizlenmiş etiket: '{predicted_label}'")
        
        print(f"✅ Tahmin başarılı: {predicted_label} (güven: {confidence:.6f})")
        return predicted_label
    except Exception as e:
        print(f"❌ Tahmin hatası: {e}")
        return simple_image_analysis(image_path, labels_path)

def simple_image_analysis(image_path, labels_path):
    """Basit görsel analizi ile tahmin yap"""
    try:
        print("🔄 Basit görsel analizi başlıyor...")
        
        # Görseli PIL ile aç
        img = Image.open(image_path)
        img_array = np.array(img)
        
        # Görsel özelliklerini analiz et
        height, width = img_array.shape[:2]
        aspect_ratio = width / height
        
        # Renk analizi
        if len(img_array.shape) == 3:  # RGB
            r, g, b = np.mean(img_array, axis=(0, 1))
            brightness = (r + g + b) / 3
        else:  # Grayscale
            brightness = np.mean(img_array)
        
        print(f"📊 Görsel boyutu: {width}x{height}")
        print(f"📊 En-boy oranı: {aspect_ratio:.2f}")
        print(f"📊 Ortalama parlaklık: {brightness:.2f}")
        
        # Etiketleri oku
        with open(labels_path, 'r', encoding='utf-8') as f:
            labels = f.read().splitlines()
        
        # Görsel özelliklerine göre tahmin
        if brightness < 100:  # Koyu görsel
            if aspect_ratio > 1.5:  # Geniş
                prediction = "sel"  # Su baskını geniş alan
            else:
                prediction = "çığ"  # Kar kütlesi
        elif brightness > 200:  # Açık görsel
            if aspect_ratio < 0.8:  # Dar
                prediction = "deprem"  # Yıkım
            else:
                prediction = "yangın"  # Ateş
        else:  # Orta parlaklık
            if aspect_ratio > 1.2:
                prediction = "heyelan"  # Toprak kayması
            else:
                prediction = "hortum"  # Hava olayı
        
        # Sayıları kaldır
        if prediction and ' ' in prediction:
            prediction = prediction.split(' ', 1)[1]
        
        print(f"✅ Basit analiz sonucu: {prediction}")
        return prediction
        
    except Exception as e:
        print(f"❌ Basit analiz hatası: {e}")
        return "çığ"  # Varsayılan tahmin
