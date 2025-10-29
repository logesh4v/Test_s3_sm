# Setup Guide - Royal Enfield S3 Chatbot

This guide will help you set up the Royal Enfield S3 Chatbot system step by step.

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Python 3.8+** installed
- [ ] **AWS Account** with access to S3 and Bedrock
- [ ] **Git** installed for cloning the repository
- [ ] **Text editor** or IDE for configuration
- [ ] **Web browser** for testing the interface

## 🚀 Step-by-Step Setup

### Step 1: Clone and Setup Project

```bash
# Clone the repository
git clone https://github.com/logesh4v/Test_s3_sm.git
cd Test_s3_sm

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: AWS Configuration

#### 2.1 Create S3 Bucket

1. **Login to AWS Console**
2. **Navigate to S3 Service**
3. **Create New Bucket**:
   - Bucket name: `your-unique-bucket-name`
   - Region: `us-east-1` (or your preferred region)
   - Keep default settings for now

#### 2.2 Create IAM User

1. **Navigate to IAM Service**
2. **Create New User**:
   - Username: `royal-enfield-chatbot-user`
   - Access type: Programmatic access
3. **Attach Policies**:
   - Create custom policy with the JSON below
   - Or attach `AmazonS3FullAccess` and `AmazonBedrockFullAccess` (less secure)

**Custom IAM Policy:**
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

4. **Save Credentials**:
   - Access Key ID
   - Secret Access Key

### Step 3: Environment Configuration

```bash
# Copy environment template
cp .env.example .env
```

**Edit `.env` file:**
```env
# AWS Configuration
AWS_ACCESS_KEY_ID=AKIA...your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-unique-bucket-name

# Model Configuration
MODEL_ID=amazon.nova-micro-v1:0
MODEL_REGION=us-east-1
MODEL_TEMPERATURE=0.7
MODEL_MAX_TOKENS=4096

# Application Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-random-secret-key-here
```

### Step 4: Prepare S3 Data (Optional)

If you have pre-processed Royal Enfield manual data:

1. **Upload to S3** with this structure:
```
your-bucket/
├── processed/
│   ├── chunks/
│   │   ├── chunk_001.json
│   │   └── ...
│   └── metadata/
│       └── document_metadata.json
```

2. **Test Data Access**:
```bash
# Test S3 connectivity
python -c "
from utils.s3_only_knowledge_base import S3OnlyKnowledgeBase
kb = S3OnlyKnowledgeBase()
print('S3 Ready:', kb.is_knowledge_base_ready())
"
```

### Step 5: Run the Application

```bash
# Start the application
python main.py
```

**Expected Output:**
```
✅ Configuration validated successfully
📚 Checking S3 knowledge base...
✅ S3 knowledge base ready with X chunks
🚀 Starting Royal Enfield Chatbot...
🌐 Web interface available at http://localhost:5000
```

### Step 6: Test the System

1. **Open Browser**: Navigate to `http://localhost:5000`
2. **Test Queries**:
   - "Check S3 knowledge base status"
   - "Show S3 health status"
   - Ask any Royal Enfield related question

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Issue: AWS Credentials Error
```
❌ Configuration Error: Missing required environment variables
```
**Solution:**
- Verify `.env` file exists and has correct AWS credentials
- Check AWS credentials are valid and not expired

#### Issue: S3 Bucket Not Accessible
```
WARNING: S3 bucket 'bucket-name' does not exist or is not accessible
```
**Solution:**
- Verify bucket name in `.env` matches actual S3 bucket
- Check IAM permissions for S3 access
- Ensure bucket exists in the specified region

#### Issue: No Knowledge Base Data
```
❌ S3 knowledge base not available
```
**Solution:**
- Upload processed data to S3 bucket
- Verify S3 folder structure matches expected format
- Check S3 permissions for reading objects

#### Issue: Bedrock Access Denied
```
❌ Bedrock model access denied
```
**Solution:**
- Verify Bedrock permissions in IAM policy
- Check if Nova Micro model is available in your region
- Ensure Bedrock service is enabled in your AWS account

### Verification Commands

```bash
# Test AWS credentials
aws sts get-caller-identity

# Test S3 access
aws s3 ls s3://your-bucket-name

# Test Python dependencies
python -c "import strands; print('Strands OK')"
python -c "import boto3; print('Boto3 OK')"
```

## 📊 Health Checks

Once running, use these features to verify system health:

1. **S3 Status**: Ask "Show S3 knowledge base status"
2. **Health Check**: Ask "Get S3 health status"
3. **Cache Refresh**: Click the ☁️ button to refresh S3 cache

## 🎯 Next Steps

After successful setup:

1. **Prepare Your Data**: Process Royal Enfield manual and upload to S3
2. **Customize Agents**: Modify agents for your specific use case
3. **Enhance UI**: Customize the web interface
4. **Add Features**: Extend with additional Strands tools
5. **Deploy**: Consider deployment to AWS Lambda or EC2

## 📞 Getting Help

If you encounter issues:

1. **Check Logs**: Look in `logs/` directory for detailed error messages
2. **Verify Configuration**: Double-check all environment variables
3. **Test Components**: Run individual agent tests
4. **AWS Console**: Verify S3 and IAM settings in AWS Console

## 🔐 Security Notes

- **Never commit** `.env` file to version control
- **Use IAM roles** instead of access keys in production
- **Enable S3 bucket encryption** for sensitive data
- **Regularly rotate** AWS access keys
- **Monitor AWS usage** to avoid unexpected charges

---

**Setup Complete!** 🎉 Your Royal Enfield S3 Chatbot should now be running successfully.