from turtle import onclick
import streamlit as st
import streamlit_modal as modal
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
import streamlit.components.v1 as components
import speech_recognisation as sr

# open_modal = st.button("Open")
# if open_modal:
#     modal.open()

# if modal.is_open():
#     with modal.container():
#         #st.write("Text goes here")

#         html_string = '''
#         <h5>Welcome to Bot</h5>
#         <script language="javascript">
#           document.querySelector("h5").style.color = "blue";
#         </script>
#         '''
#         components.html(html_string)

#         st.write("Some fancy text")
#         value = st.button(label="Speak",on_click=sr.speech_synthesis_bot)
#         st.write(f"{value}")

st = Button(label="Speak", width=100)

'''
start_bot.js_on_event("button_click", CustomJS(code="""
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
 
    recognition.onresult = function (e) {
        var value = "";
        for (var i = e.resultIndex; i < e.results.length; ++i) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
            }
        }
        if ( value != "") {
            document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
        }
    }
    recognition.start();
    """))

result = streamlit_bokeh_events(
    start_bot,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0)

if result:
    if "GET_TEXT" in result:
        st.write(result.get("GET_TEXT"))
        '''