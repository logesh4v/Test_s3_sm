# Royal Enfield S3 Chatbot - Branch Information

## Available Branches

### `main` - Initial Implementation
- Basic S3-only retrieval system
- Multi-agent architecture with Strands framework
- Web interface with Flask
- Core functionality for S3 data retrieval

### `enhanced-s3-only` - Enhanced S3 Management ✨
**Latest and Recommended Branch**

#### New Features:
- **Complete S3 Management Agent** for PDF upload and processing
- **Enhanced S3 tools** with advanced search capabilities
- **Pure S3-based architecture** (no local processing required)
- **Advanced search** with filters and options
- **Comprehensive S3 storage analytics** and management

#### Technical Improvements:
- ✅ **Fixed incomplete Strands framework integration**
- ✅ **Added S3 document lifecycle management**
- ✅ **Enhanced orchestrator agent** with proper routing
- ✅ **Improved S3Manager** with upload/process/delete operations
- ✅ **Added advanced search** with section/document filtering

#### S3 Management Features:
- 📄 **Direct PDF upload to S3**
- ⚙️ **S3-based document processing simulation**
- 📋 **Document listing and deletion**
- 📊 **Storage statistics and cost estimation**
- 🏥 **Health monitoring and status checks**

#### Architecture Benefits:
- ☁️ **Pure cloud-native S3-only system**
- 🚫 **No local file processing or storage**
- 📈 **Scalable multi-agent coordination**
- 🛡️ **Production-ready error handling**
- 📝 **Comprehensive logging and monitoring**

## Usage Recommendation

**Use the `enhanced-s3-only` branch** for:
- Production deployments
- Complete S3 document management
- Advanced search capabilities
- Full Strands framework integration

## Branch Switching

```bash
# Switch to enhanced branch
git checkout enhanced-s3-only

# Pull latest changes
git pull origin enhanced-s3-only

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Key Differences

| Feature | main | enhanced-s3-only |
|---------|------|------------------|
| S3 PDF Upload | ❌ | ✅ |
| Document Processing | ❌ | ✅ |
| Advanced Search | ❌ | ✅ |
| Storage Analytics | ❌ | ✅ |
| Complete Strands Integration | ⚠️ Partial | ✅ |
| S3 Management Agent | ❌ | ✅ |
| Document Lifecycle | ❌ | ✅ |

---

**Recommendation:** Use `enhanced-s3-only` branch for all new deployments and development.