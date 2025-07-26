#!/usr/bin/env python3

# This script uses Google Cloud Text-to-Speech API to convert text from a file to spoken audio in MP3 format.
# It supports plain text files (.txt) or PDF files (.pdf).
# It also allows listing available voices and selecting a specific voice.

# Prerequisites:
# 1. Install the required libraries: uv pip install google-cloud-texttospeech argparse pypdf2
# 2. Install the Google Cloud CLI (gcloud) if not already installed: https://cloud.google.com/sdk/docs/install
# 3. Authenticate gcloud: gcloud auth login
# 4. Enable the Text-to-Speech API: gcloud services enable texttospeech.googleapis.com

# Usage:
# - To synthesize speech: python script_name.py input_file output_audio.mp3 [--voice <voice_name>] [--language <language_code>]
#   where input_file can be a .txt or .pdf file.
# - To list voices: python script_name.py --list-voices [--language <language_code>]

# ./s2p-gcp.py --voice en-US-Wavenet-H text.txt text.mp3
# or
# ./s2p-gcp.py --voice en-US-Wavenet-H document.pdf output.mp3
# cloudshell download file.mp3

import argparse
import sys
import os
from google.cloud import texttospeech
import PyPDF2

def list_voices(language_code):
    try:
        client = texttospeech.TextToSpeechClient()
    except Exception as e:
        print(f"Error creating client: {e}")
        sys.exit(1)
    try:
        response = client.list_voices(language_code=language_code)
        for voice in response.voices:
            print(f"Name: {voice.name}")
            print(f"Languages: {', '.join(voice.language_codes)}")
            print(f"Gender: {texttospeech.SsmlVoiceGender(voice.ssml_gender).name}")
            print(f"Natural Sample Rate Hertz: {voice.natural_sample_rate_hertz}")
            print("---")
    except Exception as e:
        print(f"Error listing voices: {e}")
        sys.exit(1)

def text_to_speech(input_file, output_file, voice_name, language_code):
    # Determine file type
    file_ext = os.path.splitext(input_file)[1].lower()
    
    # Read the text from the input file
    text = ''
    try:
        if file_ext == '.txt':
            with open(input_file, 'r', encoding='utf-8') as f:
                text = f.read()
        elif file_ext == '.pdf':
            with open(input_file, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
        else:
            print(f"Error: Unsupported file type '{file_ext}'. Only .txt and .pdf are supported.")
            sys.exit(1)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)

    if not text.strip():
        print("Error: No text extracted from the input file.")
        sys.exit(1)

    # Instantiates a client
    try:
        client = texttospeech.TextToSpeechClient()
    except Exception as e:
        print(f"Error creating client: {e}")
        sys.exit(1)
    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Build the voice request
    # When specifying a voice name, the gender is implied by the voice, so we omit ssml_gender here
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice_name
    )

    # Select the type of audio file you want returned (MP3)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Perform the text-to-speech request
    try:
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
    except Exception as e:
        print(f"Error during synthesis: {e}")
        sys.exit(1)

    # Write the response to the output file
    try:
        with open(output_file, "wb") as out:
            out.write(response.audio_content)
        print(f"Audio content written to file '{output_file}'")
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Text-to-Speech using Google Cloud API")
    parser.add_argument('input_file', nargs='?', help="Input text or PDF file")
    parser.add_argument('output_file', nargs='?', help="Output MP3 file")
    parser.add_argument('--list-voices', action='store_true', help="List available voices and exit")
    parser.add_argument('--voice', default="en-US-Wavenet-D", help="Voice name to use (default: en-US-Wavenet-D)")
    parser.add_argument('--language', default="en-US", help="Language code (default: en-US)")

    args = parser.parse_args()

    if args.list_voices:
        list_voices(args.language)
    elif not args.input_file or not args.output_file:
        parser.print_help()
        sys.exit(1)
    else:
        text_to_speech(args.input_file, args.output_file, args.voice, args.language)
