import logging
import sys
import os


def setup_logger():
    """
    Uygulama genelinde kullanılacak olan logger'ı yapılandırır.
    Logları hem konsola hem de 'app.log' adında bir dosyaya yazar.
    """
    # Log dosyasının yolu
    log_file = 'app.log'

    # Formatter oluştur: logların nasıl görüneceğini belirler
    log_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )

    # Root logger'ı al
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Kaydedilecek minimum log seviyesi

    # Mevcut handler'ları temizle (eğer varsa, çift loglamayı önler)
    if logger.hasHandlers():
        logger.handlers.clear()

    # Konsol handler'ı oluştur ve formatı ayarla
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(log_formatter)
    logger.addHandler(stdout_handler)

    # Dosya handler'ı oluştur ve formatı ayarla
    # 'a' modu: dosyanın sonuna ekler, 'w' modu: üzerine yazar
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

    return logger


# Uygulamanın her yerinden erişilebilecek tek bir logger nesnesi oluştur
logger = setup_logger()
