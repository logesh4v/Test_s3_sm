# Royal Enfield S3 Knowledge Base Chatbot - S3 V3

A sophisticated **S3-based multi-agent chatbot system** built with the **Strands framework** that processes Royal Enfield Meteor owner's manual PDFs with **real local processing** and provides intelligent conversational access to motorcycle information.

## 🎯 Version 3.0.0 (S3-V3) - Real PDF Processing

**Key Innovation:** PDFs uploaded to S3 are **downloaded, processed locally, and results uploaded back** to S3 for intelligent search and chat.

## 🚀 Key Features (S3-V3)

- **🔄 Real PDF Processing**: Downloads PDFs from S3, processes locally with text extraction, uploads chunks back
- **📄 Complete Document Lifecycle**: Upload → Process → Search → Delete with full S3 management
- **🤖 Multi-Agent System**: Built with Strands framework using specialized agents
- **🔍 Advanced Search**: Intelligent search with filters, relevance scoring, and section-based queries
- **💬 Conversational AI**: Natural language chat with context awareness and source citations
- **🌐 Modern Web Interface**: Responsive chat interface with real-time messaging
- **📊 S3 Analytics**: Comprehensive storage statistics, cost estimation, and health monitoring
- **⚡ Intelligent Chunking**: Smart text chunking with overlap, topic extraction, and metadata

## 🏗️ S3-V3 Processing Architecture

The system uses a **hybrid S3 + local processing architecture** with specialized Strands agents:

### 🔄 Processing Flow
```
S3 PDF Upload → Download to Local → Text Extraction → Intelligent Chunking → Upload Chunks to S3 → Search & Chat
```

### 🤖 Specialized Agents
- **🎯 Orchestrator Agent**: Routes requests to appropriate specialized agents
- **📄 S3 Management Agent**: Handles PDF upload, processing, and document lifecycle
- **🔎 Retrieval Agent**: Performs advanced search on processed S3 data
- **💭 Chat Agent**: Manages conversational interactions with processed context
- **📊 S3 Manager**: Handles all AWS S3 operations and health monitoring

## 📁 Project Structure

```
royal-enfield-chatbot/
├── agents/                    # Strands agents
│   ├── orchestrator_agent.py # Main request router
│   ├── retrieval_agent.py    # S3 search and retrieval
│   └── chat_agent.py         # Conversational interface
├── tools/                     # Custom Strands tools
│   ├── s3_only_tools.py      # S3-specific retrieval tools
│   └── chat_tools.py         # Chat and conversation tools
├── utils/                     # Core utilities
│   ├── s3_only_knowledge_base.py # S3-only knowledge base
│   ├── s3_client.py          # Low-level S3 operations
│   ├── s3_manager.py         # High-level S3 management
│   └── pdf_processor.py      # PDF processing utilities
├── web/                       # Flask web interface
│   ├── app.py                # Main Flask application
│   └── templates/
│       └── index.html        # Modern chat interface
├── config/                    # Configuration management
│   └── settings.py           # Environment-based configuration
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── main.py                   # Application entry point
└── README.md                 # This documentation
```

## ☁️ S3 Data Structure

The system expects pre-processed data in your S3 bucket with this structure:

```
your-s3-bucket/
├── processed/
│   ├── chunks/               # Pre-processed text chunks (JSON files)
│   │   ├── chunk_001.json
│   │   ├── chunk_002.json
│   │   └── ...
│   └── metadata/             # Document metadata
│       └── document_metadata.json
├── documents/                # Original PDF files (optional)
│   └── royal-enfield-meteor-manual.pdf
└── indexes/                  # Search indexes (optional)
    └── search_index.json
```

## ⚙️ Quick Setup

### 1. Prerequisites

- **Python 3.8+**
- **AWS Account** with S3 and Bedrock access
- **Pre-processed Royal Enfield manual data in S3**

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/logesh4v/Test_s3_sm.git
cd Test_s3_sm

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env
```

**Edit `.env` with your AWS settings:**

```env
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-s3-bucket-name

# Model Configuration
MODEL_ID=amazon.nova-micro-v1:0
MODEL_REGION=us-east-1
MODEL_TEMPERATURE=0.7
MODEL_MAX_TOKENS=4096

# Application Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your_secret_key_here
```

### 4. AWS IAM Permissions

Create an IAM user with these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name",
                "arn:aws:s3:::your-bucket-name/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel"
            ],
            "Resource": "arn:aws:bedrock:*:*:foundation-model/amazon.nova-micro-v1:0"
        }
    ]
}
```

## 🚀 Running the Application

```bash
# Start the application
python main.py
```

The application will:
- ✅ Validate AWS configuration
- ☁️ Check S3 bucket connectivity
- 🌐 Start web interface at `http://localhost:5000`

## 💬 Using the Chatbot

### Web Interface
1. Open `http://localhost:5000` in your browser
2. Start asking questions about your Royal Enfield Meteor
3. Get intelligent responses with source citations

### Example Queries
- "How do I change the engine oil?"
- "What are the brake specifications?"
- "Show me troubleshooting steps for starting problems"
- "What's the maintenance schedule?"
- "Check S3 knowledge base status"

## 🔧 S3-Specific Features

### Available Tools
- **S3 Search**: `search_s3_knowledge_base` - Search through S3-stored chunks
- **Contextual Info**: `get_contextual_information_s3` - Get aggregated context
- **Section Search**: `search_by_section_s3` - Search specific manual sections
- **Page Search**: `search_by_page_s3` - Find content from specific pages
- **Health Status**: `get_s3_health_status` - Check S3 connectivity and data
- **Cache Management**: `clear_s3_cache` - Refresh cached S3 data

### S3 Health Monitoring
- Real-time S3 connection status
- Storage statistics and usage
- Data availability verification
- Permission validation
- Cache performance metrics

## 🛠️ Development

### Testing Components

```bash
# Test individual agents
python agents/retrieval_agent.py
python agents/chat_agent.py
python agents/orchestrator_agent.py
```

### S3 Data Preparation

To prepare your own S3 knowledge base:

1. **Process PDF**: Extract text and create chunks
2. **Upload to S3**: Store chunks in `processed/chunks/` folder
3. **Add Metadata**: Include document metadata in `processed/metadata/`
4. **Test Access**: Verify S3 permissions and data structure

## 📊 Monitoring & Debugging

### Logs
- Application logs in `logs/` directory
- S3 operation logs and performance metrics
- Agent interaction and decision logs
- User query and response logs

### Health Checks
- S3 connectivity status
- Data availability verification
- Cache performance monitoring
- Agent response times

## 🔍 Troubleshooting

### Common Issues

**S3 Connection Issues:**
- Verify AWS credentials in `.env`
- Check S3 bucket permissions
- Ensure bucket exists and is accessible

**No Search Results:**
- Verify processed data exists in S3
- Check S3 bucket structure matches expected format
- Use "Check S3 Status" to verify data availability

**Performance Issues:**
- Use cache refresh to clear stale data
- Check S3 region configuration
- Monitor S3 request rates

## 🎯 Key Benefits

- ✅ **No Local Processing**: Pure S3-based data retrieval
- ✅ **Cloud-Native**: Fully leverages AWS S3 capabilities
- ✅ **Scalable**: Handles large knowledge bases efficiently
- ✅ **Fast Startup**: No PDF processing overhead
- ✅ **Multi-Instance**: Multiple deployments can share S3 data
- ✅ **Cost-Effective**: Pay only for S3 storage and requests

## 🤝 Contributing

This project demonstrates advanced **Strands framework** usage with:
- Multi-agent coordination
- Custom tool development
- AWS service integration
- Real-world application architecture

Contributions welcome for:
- Enhanced search algorithms
- Additional S3 optimizations
- UI/UX improvements
- Performance enhancements

## 📄 License

Educational and demonstration project for Strands framework and AWS S3 integration.

## 🆘 Support

For issues:
1. Check S3 connectivity and permissions
2. Verify data structure in S3 bucket
3. Review application logs
4. Use built-in health status tools

---

**Built with ❤️ using [Strands Framework](https://strands.ai) and AWS S3**