import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import api from '../../src/services/api';

interface Subject {
  subject: string;
  name: string;
  icon: string;
}

interface Message {
  id: string;
  type: 'user' | 'gyan';
  text: string;
  subject?: string;
  confidence?: number;
  sources?: string[];
  timestamp: Date;
}

export default function GyanMindScreen() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectedSubject, setSelectedSubject] = useState<string>('general');
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [questionsRemaining, setQuestionsRemaining] = useState(10);
  const scrollViewRef = useRef<ScrollView>(null);

  useEffect(() => {
    fetchSubjects();
    // Add welcome message
    setMessages([{
      id: '1',
      type: 'gyan',
      text: '🙏 नमस्ते! Main aapka Gyan Mind Trigger hoon। Koi bhi sawaal poochho - Mathematics, Science, Law, Health, ya kuch bhi! Main aapki madad ke liye yahan hoon।',
      timestamp: new Date()
    }]);
  }, []);

  const fetchSubjects = async () => {
    try {
      const response = await api.get('/ai-teacher/subjects');
      setSubjects(response.data.subjects);
      setQuestionsRemaining(response.data.config?.max_questions_per_day_free || 10);
    } catch (error) {
      console.error('Error fetching subjects:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      text: inputText,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await api.post('/ai-teacher/ask', {
        subject: selectedSubject,
        question: inputText,
        language: 'Hindi'
      });

      if (response.data.success) {
        const gyanMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'gyan',
          text: response.data.answer,
          subject: response.data.subject,
          confidence: response.data.confidence_score,
          sources: response.data.sources,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, gyanMessage]);
        setQuestionsRemaining(response.data.questions_remaining);
      } else {
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'gyan',
          text: response.data.message || 'Kuch galat ho gaya. Kripya dobara try karein.',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'gyan',
        text: 'Network error. Kripya apna internet connection check karein.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const renderMessage = (message: Message) => {
    const isUser = message.type === 'user';
    
    return (
      <View
        key={message.id}
        style={[
          styles.messageContainer,
          isUser ? styles.userMessageContainer : styles.gyanMessageContainer
        ]}
      >
        {!isUser && (
          <View style={styles.gyanAvatar}>
            <Text style={styles.gyanAvatarText}>🧠</Text>
          </View>
        )}
        <View style={[
          styles.messageBubble,
          isUser ? styles.userBubble : styles.gyanBubble
        ]}>
          <Text style={[
            styles.messageText,
            isUser ? styles.userMessageText : styles.gyanMessageText
          ]}>
            {message.text}
          </Text>
          
          {message.confidence && (
            <View style={styles.confidenceContainer}>
              <Text style={styles.confidenceText}>
                Gyan Score: {(message.confidence * 100).toFixed(0)}%
              </Text>
            </View>
          )}
          
          {message.sources && message.sources.length > 0 && (
            <View style={styles.sourcesContainer}>
              <Text style={styles.sourcesTitle}>📚 Sources:</Text>
              {message.sources.map((source, index) => (
                <Text key={index} style={styles.sourceText}>• {source}</Text>
              ))}
            </View>
          )}
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#1A1A2E', '#16213E', '#0F3460']}
        style={styles.gradient}
      >
        <SafeAreaView style={styles.safeArea}>
          {/* Header */}
          <View style={styles.header}>
            <View style={styles.headerLeft}>
              <Text style={styles.headerIcon}>🧠</Text>
              <View>
                <Text style={styles.headerTitle}>Gyan Mind Trigger</Text>
                <Text style={styles.headerSubtitle}>Mind Trigger System</Text>
              </View>
            </View>
            <View style={styles.questionsCounter}>
              <Ionicons name="help-circle" size={16} color="#FFD700" />
              <Text style={styles.questionsText}>{questionsRemaining} left</Text>
            </View>
          </View>

          {/* Subject Selector */}
          <ScrollView 
            horizontal 
            showsHorizontalScrollIndicator={false}
            style={styles.subjectScroll}
            contentContainerStyle={styles.subjectContainer}
          >
            {subjects.map((subject) => (
              <TouchableOpacity
                key={subject.subject}
                style={[
                  styles.subjectChip,
                  selectedSubject === subject.subject && styles.subjectChipActive
                ]}
                onPress={() => setSelectedSubject(subject.subject)}
              >
                <Text style={styles.subjectIcon}>{subject.icon}</Text>
                <Text style={[
                  styles.subjectText,
                  selectedSubject === subject.subject && styles.subjectTextActive
                ]}>
                  {subject.name.split(' ')[0]}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          {/* Chat Messages */}
          <ScrollView
            ref={scrollViewRef}
            style={styles.chatContainer}
            contentContainerStyle={styles.chatContent}
            onContentSizeChange={() => scrollViewRef.current?.scrollToEnd()}
          >
            {messages.map(renderMessage)}
            
            {isLoading && (
              <View style={styles.loadingContainer}>
                <View style={styles.gyanAvatar}>
                  <Text style={styles.gyanAvatarText}>🧠</Text>
                </View>
                <View style={styles.typingBubble}>
                  <ActivityIndicator size="small" color="#FFD700" />
                  <Text style={styles.typingText}>Gyan Mind processing...</Text>
                </View>
              </View>
            )}
          </ScrollView>

          {/* Input Area */}
          <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          >
            <View style={styles.inputContainer}>
              <TextInput
                style={styles.textInput}
                placeholder="Apna sawaal yahan likhein..."
                placeholderTextColor="#808080"
                value={inputText}
                onChangeText={setInputText}
                multiline
                maxLength={500}
              />
              <TouchableOpacity
                style={[
                  styles.sendButton,
                  (!inputText.trim() || isLoading) && styles.sendButtonDisabled
                ]}
                onPress={sendMessage}
                disabled={!inputText.trim() || isLoading}
              >
                <LinearGradient
                  colors={inputText.trim() && !isLoading ? ['#FFD700', '#FFA500'] : ['#404040', '#303030']}
                  style={styles.sendButtonGradient}
                >
                  <Ionicons 
                    name="send" 
                    size={20} 
                    color={inputText.trim() && !isLoading ? '#1A1A2E' : '#808080'} 
                  />
                </LinearGradient>
              </TouchableOpacity>
            </View>
          </KeyboardAvoidingView>
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0A0A0F',
  },
  gradient: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 215, 0, 0.1)',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  headerIcon: {
    fontSize: 32,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  headerSubtitle: {
    fontSize: 12,
    color: '#FFD700',
  },
  questionsCounter: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 215, 0, 0.1)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    gap: 4,
  },
  questionsText: {
    fontSize: 12,
    color: '#FFD700',
    fontWeight: '600',
  },
  subjectScroll: {
    maxHeight: 60,
  },
  subjectContainer: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    gap: 8,
  },
  subjectChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
    gap: 6,
  },
  subjectChipActive: {
    backgroundColor: 'rgba(255, 215, 0, 0.2)',
    borderWidth: 1,
    borderColor: '#FFD700',
  },
  subjectIcon: {
    fontSize: 16,
  },
  subjectText: {
    fontSize: 12,
    color: '#A0A0A0',
  },
  subjectTextActive: {
    color: '#FFD700',
    fontWeight: '600',
  },
  chatContainer: {
    flex: 1,
  },
  chatContent: {
    padding: 16,
    paddingBottom: 20,
  },
  messageContainer: {
    flexDirection: 'row',
    marginBottom: 16,
    alignItems: 'flex-start',
  },
  userMessageContainer: {
    justifyContent: 'flex-end',
  },
  gyanMessageContainer: {
    justifyContent: 'flex-start',
  },
  gyanAvatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 215, 0, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  gyanAvatarText: {
    fontSize: 20,
  },
  messageBubble: {
    maxWidth: '75%',
    padding: 12,
    borderRadius: 16,
  },
  userBubble: {
    backgroundColor: '#FFD700',
    borderBottomRightRadius: 4,
    marginLeft: 'auto',
  },
  gyanBubble: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderBottomLeftRadius: 4,
  },
  messageText: {
    fontSize: 14,
    lineHeight: 20,
  },
  userMessageText: {
    color: '#1A1A2E',
  },
  gyanMessageText: {
    color: '#FFFFFF',
  },
  confidenceContainer: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.1)',
  },
  confidenceText: {
    fontSize: 10,
    color: '#4CAF50',
  },
  sourcesContainer: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.1)',
  },
  sourcesTitle: {
    fontSize: 10,
    color: '#FFD700',
    marginBottom: 4,
  },
  sourceText: {
    fontSize: 10,
    color: '#808080',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  typingBubble: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    padding: 12,
    borderRadius: 16,
    gap: 8,
  },
  typingText: {
    fontSize: 12,
    color: '#A0A0A0',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 215, 0, 0.1)',
    gap: 12,
  },
  textInput: {
    flex: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 12,
    color: '#FFFFFF',
    fontSize: 14,
    maxHeight: 100,
  },
  sendButton: {
    borderRadius: 24,
    overflow: 'hidden',
  },
  sendButtonDisabled: {
    opacity: 0.5,
  },
  sendButtonGradient: {
    width: 48,
    height: 48,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
