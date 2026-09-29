// Web Speech API Types
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

export class VoiceInputService {
  private recognition: any;
  private isListeningState = false;
  private onTranscript: (text: string) => void;
  private onErrorCb: (error: string) => void;
  private onEndCb: () => void;

  constructor(
    onTranscript: (text: string) => void,
    onError: (error: string) => void,
    onEnd: () => void
  ) {
    this.onTranscript = onTranscript;
    this.onErrorCb = onError;
    this.onEndCb = onEnd;
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = false;

      this.recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        this.onTranscript(transcript);
      };

      this.recognition.onerror = (event: any) => {
        this.isListeningState = false;
        this.onErrorCb(event.error);
      };

      this.recognition.onend = () => {
        this.isListeningState = false;
        this.onEndCb();
      };
    } else {
      console.warn("SpeechRecognition API not supported in this browser.");
    }
  }

  startListening(language: string) {
    if (!this.recognition) {
      this.onErrorCb('browser-unsupported');
      return;
    }
    try {
      this.recognition.lang = language;
      this.recognition.start();
      this.isListeningState = true;
    } catch (e) {
      console.error(e);
      this.isListeningState = false;
      this.onErrorCb('start-failed');
    }
  }

  stopListening() {
    if (this.recognition && this.isListeningState) {
      this.recognition.stop();
      this.isListeningState = false;
    }
  }

  isListening() {
    return this.isListeningState;
  }
}

export class VoiceOutputService {
  private synth: SpeechSynthesis;
  private isSpeakingState = false;

  constructor() {
    this.synth = window.speechSynthesis;
  }

  speak(text: string, language: string, onEnd?: () => void) {
    if (!this.synth) return;

    this.stop(); // Stop any ongoing speech

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = language;
    
    // Find the best matching voice for the requested language
    const voices = this.synth.getVoices();
    const langPrefix = language.split('-')[0]; // e.g. "kn" from "kn-IN"
    
    // Priority 1: exact match (e.g. "kn-IN" === "kn-IN")
    let matchingVoice = voices.find(v => v.lang === language);
    
    // Priority 2: same language prefix (e.g. "kn-IN" starts with "kn")
    if (!matchingVoice) {
      matchingVoice = voices.find(v => v.lang.startsWith(langPrefix + '-') || v.lang === langPrefix);
    }
    
    // Priority 3: any voice whose lang starts with the prefix
    if (!matchingVoice) {
      matchingVoice = voices.find(v => v.lang.toLowerCase().startsWith(langPrefix.toLowerCase()));
    }
    
    if (matchingVoice) {
      utterance.voice = matchingVoice;
      console.log(`[TTS] Selected voice: ${matchingVoice.name} (${matchingVoice.lang}) for requested language: ${language}`);
    } else {
      console.warn(`[TTS] No matching voice found for language: ${language} (prefix: ${langPrefix}). Available: ${voices.map(v => v.lang).join(', ')}. Falling back to browser default.`);
    }
    
    utterance.onstart = () => {
      this.isSpeakingState = true;
    };
    
    utterance.onend = () => {
      this.isSpeakingState = false;
      if (onEnd) onEnd();
    };

    utterance.onerror = (e) => {
      console.error('[TTS] Error', e);
      this.isSpeakingState = false;
      if (onEnd) onEnd();
    };

    this.synth.speak(utterance);
  }

  stop() {
    if (this.synth) {
      this.synth.cancel();
      this.isSpeakingState = false;
    }
  }

  isSpeaking() {
    return this.isSpeakingState;
  }
}
