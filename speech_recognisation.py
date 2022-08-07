import azure.cognitiveservices.speech as speechsdk
import time
import pandas as pd
import pickle
import streamlit as st

subscription_key = "56b6cd274cc944be99f8bde7ae202a0c"
region = "centralindia"
table_file = "f282ec8a-7a36-4b26-866c-4619aa858a87.table"
custom_keyword = "Hey Bot"

bot_flow_df = pd.read_csv('bot_neural_flow_new.csv')
vehicle_data = pd.read_csv('data.csv')

# pickle model
with open('bot_neural_flow.model', 'wb') as fh:
   pickle.dump(bot_flow_df, fh)
pickle_off = open("bot_neural_flow.model", "rb")
bot_flow_df = pickle.load(pickle_off)

bot_flow_df_copy = bot_flow_df
# bot first reply text, sampling can be done
bot_first_reply_df = bot_flow_df[bot_flow_df['FirstReply']==1]
bot_first_reply_dict = bot_first_reply_df.to_dict('records')[0]
bot_first_reply_text = bot_first_reply_dict['Field']
bot_flow_dict = bot_flow_df.to_dict('records')
user_mic_data = []
vehicle_no = []
import re

def recognize_from_microphone():
    speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
    speech_config.speech_recognition_language="en-US"

    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    print("Speak into your microphone.")
    st.write("Speak into your microphone.")
    speech_recognition_result = speech_recognizer.recognize_once_async().get()

    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print("{}".format(speech_recognition_result.text))
        st.write("{}".format(speech_recognition_result.text))
        return "{}".format(speech_recognition_result.text)
    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_recognition_result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
            print("Did you set the speech resource key and region values?")
    
def speech_recognize_keyword_from_microphone():
    """performs keyword-triggered speech recognition with input microphone"""
    speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)

    # Creates an instance of a keyword recognition model. Update this to
    # point to the location of your keyword recognition model.
    model = speechsdk.KeywordRecognitionModel(table_file)

    # The phrase your keyword recognition model triggers on.
    keyword = custom_keyword

    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

    done = False

    def stop_cb(evt):
        """callback that signals to stop continuous recognition upon receiving an event `evt`"""
        print('CLOSING on {}'.format(evt))
        nonlocal done
        done = True

    def recognizing_cb(evt):
        """callback for recognizing event"""
        if evt.result.reason == speechsdk.ResultReason.RecognizingKeyword:
            print('RECOGNIZING KEYWORD: {}'.format(evt))
            # after keyword recognise, recognize from microphone
            # recognize_from_microphone()
        elif evt.result.reason == speechsdk.ResultReason.RecognizingSpeech:
            print('RECOGNIZING: {}'.format(evt))

    def recognized_cb(evt):
        """callback for recognized event"""
        if evt.result.reason == speechsdk.ResultReason.RecognizedKeyword:
            print('RECOGNIZED KEYWORD: {}'.format(evt))
        elif evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print('RECOGNIZED: {}'.format(evt))
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            print('NOMATCH: {}'.format(evt))

    # Connect callbacks to the events fired by the speech recognizer
    speech_recognizer.recognizing.connect(recognizing_cb)
    speech_recognizer.recognized.connect(recognized_cb)
    
    speech_recognizer.session_started.connect(lambda evt: print('SESSION STARTED: {}'.format(evt)))
    speech_recognizer.session_stopped.connect(lambda evt: print('SESSION STOPPED {}'.format(evt)))
    speech_recognizer.canceled.connect(lambda evt: print('CANCELED {}'.format(evt)))
    # stop continuous recognition on either session stopped or canceled events
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    # Start keyword recognition
    speech_recognizer.start_keyword_recognition(model)
    print('Say something starting with "{}" followed by whatever you want...'.format(keyword))
    st.write('Say something starting with "{}" followed by whatever you want...'.format(keyword))
    while not done:
        time.sleep(.5)
    speech_recognizer.stop_keyword_recognition()
    return bot_first_reply_text

def speech_synthesis_bot(*args):
    speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

    # The language of the voice that speaks.
    speech_config.speech_synthesis_voice_name='en-US-JennyNeural'
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    # earlier it was taking input from keyboard, now input is from microphone
    if len(args)==0:
        text = speech_recognize_keyword_from_microphone()
        text_final = text
    print(len(args))
    # data = {"Field":text[text.find("{")+1:text.find("}")],"Value":""}
    if len(args)>0:
        Id = args[0]
        if len(args)==3:
            cbrid = args[1]
        if Id==0:
            text_0 = bot_flow_df[bot_flow_df['Id']==0].to_dict('records')[0]['Field']
            # print(text,'value no available')
            speech_synthesis_result = speech_synthesizer.speak_text_async(text_0).get()
            text = bot_flow_df[bot_flow_df['Id']==cbrid].to_dict('records')[0]['Field']
            text_final = args[2]
        elif Id!=0 and Id!=-1:
            text = bot_flow_df[bot_flow_df['Id']==Id].to_dict('records')[0]['Field']
            s = "{"+text[text.find("{")+1:text.find("}")]+"}"
            if text[text.find("{")+1:text.find("}")]=='vehicle_number':
                vehicle_no.append(args[2])
                # print(vehicle_no)
            # print(s,'avail')
            text_final = text.replace(s,args[2])
            # print(text,'value available')
            if args[1]=='':
                if type(args[2])==str:
                    text = bot_flow_df[bot_flow_df['Id']==Id].to_dict('records')[0]['Field']
                    s = "{"+text[text.find("{")+1:text.find("}")]+"}"
                    # print(s,'here')
                    text_final = text.replace(s,args[2])
        elif Id==-1:
            text_final = 'Data not available for this vehicle!!'
            speech_synthesis_result = speech_synthesizer.speak_text_async(text_final).get()
            speech_synthesis_bot()
    print("{}".format(text_final))
    st.write("Bot: "+"{}".format(text_final))
    speech_synthesis_result = speech_synthesizer.speak_text_async(text_final).get()
    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        # get input from microphone
        input_from_mic = recognize_from_microphone()
        input_from_mic = input_from_mic.replace('.','')
        bot_reply_value = bot_flow_df[bot_flow_df['Field']=="{}".format(text)]
        current_bot_reply_id = bot_reply_value.to_dict('records')[0]['Id']
        negative_feedback_value = bot_flow_df[bot_flow_df['Field']=="{}".format(text)].to_dict('records')[0]['NegativeFeedbackValue']
        negative_feedback_backtrack_id = bot_flow_df[bot_flow_df['Field']=="{}".format(text)].to_dict('records')[0]['NegativeFeedbackBacktrackId']
        data_from_backend = bot_flow_df[bot_flow_df['Field']=="{}".format(text)].to_dict('records')[0]['DataFromBackend']
        bot_reply_value = bot_reply_value.to_dict('records')[0]['Value']
        print('data from backend',data_from_backend)
        # print(bot_reply_value)
        bot_reply_list = 'noval'
        if type(bot_reply_value)==str:
            bot_reply_list = bot_reply_value.split(',')
        elif type(bot_reply_value)==float:
            bot_reply_list = []

        if input_from_mic in bot_reply_list:
            if negative_feedback_value==input_from_mic:
                current_bot_reply_id=negative_feedback_backtrack_id
                speech_synthesis_bot(negative_feedback_backtrack_id,'',input_from_mic)
            print('Right!')
            if data_from_backend==1:
                v_no = vehicle_no[0].replace(' ','')
                print(v_no)
                v_data = vehicle_data[vehicle_data['VehicleNo']==v_no]
                v_data = v_data.to_dict('records')
                # print(v_data[0]['InsurancePrice'])
                if len(v_data)==0:
                    speech_synthesis_bot(-1,'',input_from_mic)
                elif len(v_data)>0:
                    speech_synthesis_bot(current_bot_reply_id+1,'',str(v_data[0]['InsurancePrice']))
            else:
                speech_synthesis_bot(current_bot_reply_id+1,'',input_from_mic)
        elif len(bot_reply_list)==0:
            print('No Value to Split!!')
            speech_synthesis_bot(current_bot_reply_id+1,'',input_from_mic)
        else:
            speech_synthesis_bot(0,current_bot_reply_id,text_final)
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print("Error details: {}".format(cancellation_details.error_details))
                print("Did you set the speech resource key and region values?")

try:
    speech_synthesis_bot()
except Exception as e:
    print(e)
    speech_synthesis_bot()