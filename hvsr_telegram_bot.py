import logging
import os
import io
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
import requests
from telegram import Update, InputMediaPhoto
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import obspy
import numpy as np

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up Obspy trace handling function
def process_mseed_file(file_path):
    # Load the mseed file using obspy
    st = obspy.read(file_path)

    # Print out the list of traces in the stream
    print(st)
    
    # Filter the data to keep only the frequency band of interest
    #fmin, fmax = 0.8, 10.0 # set the frequency band of interest
    #st.filter('bandpass', freqmin=fmin, freqmax=fmax)

    # Menghitung rentang frequency (untuk plot sumbu x)
    npts = st[0].stats.npts 
    dt = st[0].stats.delta                  
    fNy = 1. / (2. * dt)                     
    freq = np.linspace(0, fNy, npts // 2 + 1)

    # FFT (sumbu y)
    amp = np.fft.rfft(st[0].data)

    # Plot the H/V Spectral Ratio graph
    plt.plot(freq, abs(amp), 'k')
    plt.title('Fast Fourier Transform \n FFT')
    plt.ylabel('Amplitude')
    plt.xlabel('Frequency (Hz)')
    plt.xlim(0,5)

    # Save the figure to a PNG file
    plt.savefig('hvsr_graph.png')
    plt.clf()
    plt.close()
    img = "hvsr_graph.png"
    return img

def handle_start(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info(f"{user.first_name} {user.last_name} started the bot")
    update.message.reply_text("Hello! Send me an mseed file and I will generate a frequency dominant graph for you.")


# Set up Telegram bot handling function
def handle_document(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info(f"{user.first_name} {user.last_name} sent a file: {update.message.document.file_name}")

    # Get the file ID and file name
    file_id = update.message.document.file_id
    file_name = update.message.document.file_name

    # Download the file
    file_info = context.bot.get_file(file_id)
    download_url = file_info.file_path
    response = requests.get(download_url)

    # Save the file to disk
    with open(file_name, 'wb') as f:
        f.write(response.content)

    # Process the file
    img = process_mseed_file(file_name)

    # Load the image
    with open(img, 'rb') as img_file:
        img_bytes = img_file.read()

    # Send the image back to the user
    context.bot.send_media_group(update.message.chat_id, [InputMediaPhoto(media=io.BytesIO(img_bytes))])

    # Clean up
    os.remove(img)
    os.remove(file_name)
    

def main():
    updater = Updater("6806314135:AAFsapiS9l9R8_AE73Dn2ZYCvtLlRn_PMfI", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", handle_start))
    dp.add_handler(MessageHandler(Filters.document, handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
