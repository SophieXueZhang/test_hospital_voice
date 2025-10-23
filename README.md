# 🏥 Hospital Management Dashboard

A comprehensive healthcare analytics dashboard built with Streamlit for visualizing patient data, medical indicators, and operational metrics.

## ✨ Features

- **📊 KPI Overview**: Average length of stay, readmission rates, bed turnover
- **🏥 Department Comparison**: Performance metrics across different departments
- **🔬 Medical Analytics**: Laboratory indicators vs patient outcomes
- **📈 Trend Analysis**: Time-based analytics and benchmarking
- **👤 Patient Details**: Individual patient records with clickable navigation
- **🔍 Advanced Search**: Multi-criteria patient search and filtering
- **🤖 AI Chat Assistant**: Healthcare AI for data insights and explanations
- **🎙️ Real-time Voice Chat**: Interactive voice conversations with AI using OpenAI Realtime API

## 🎨 Design

- Nordic minimalist design aesthetic
- Interactive visualizations with Plotly
- Responsive layout with custom CSS
- Color-coded risk levels and metrics

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up OpenAI API key (required for voice chat)
export OPENAI_API_KEY="your-api-key-here"

# Run the application
streamlit run app.py
```

### 🎙️ Voice Chat Features

The application includes two types of voice interaction:

1. **Text Chat with Voice Input** (💬 button, right side)
   - Click the microphone icon in the chat window
   - Speak your question
   - Get text and voice responses
   - Uses Web Speech API + OpenAI TTS

2. **Real-time Voice Chat** (🎤 button, left side)
   - Click the microphone button to start
   - Have a natural voice conversation with AI
   - Real-time streaming audio responses
   - Uses OpenAI Realtime API
   - Shows conversation transcript

**Requirements:**
- OpenAI API key must be set in environment variables
- Modern web browser (Chrome/Edge recommended)
- Microphone access permission

**Usage:**
1. Navigate to any patient detail page
2. Click the 🎤 button (left) for real-time voice chat
3. Or click the 💬 button (right) for text chat with voice input
4. Grant microphone permission when prompted
5. Start speaking naturally!

## 📱 Access

- **Local**: http://localhost:8501
- **Network**: http://192.168.1.113:8501

## 🛠 Technology Stack

- **Frontend**: Streamlit
- **Visualization**: Plotly, Pandas
- **AI Integration**: OpenAI ChatGPT API
- **Styling**: Custom CSS with Nordic design principles

## 📊 Data Features

- 100,000+ patient records
- Real-time filtering and search
- Risk level categorization
- Age group analytics
- Multi-dimensional data exploration

## 🔒 Privacy Note

This dashboard uses synthetic healthcare data for demonstration purposes.

---

Built with ❤️ using Streamlit