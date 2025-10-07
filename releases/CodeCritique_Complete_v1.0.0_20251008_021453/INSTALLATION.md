# CodeCritique Installation Guide

## 🚀 Quick Installation

### Windows
1. **Extract the ZIP file** to your desired location
2. **Double-click `start.bat`** to start the application
3. **Open your browser** and go to http://localhost:5000

### Linux/Mac
1. **Extract the ZIP file** to your desired location
2. **Run `./start.sh`** in terminal to start the application
3. **Open your browser** and go to http://localhost:5000

## 🔧 Advanced Setup

### **Custom Configuration**
- Edit files in `config/` directory to customize settings
- Modify `config/app_config.json` for application settings
- Update `config/roles.json` for role definitions
- Customize `config/checklist_columns.json` for checklist structure

### **Network Deployment**
- Configure `config/network_security.json` for network settings
- Set up proxy settings if needed
- Configure firewall rules for port 5000
- Set up SSL certificates for HTTPS

### **Enterprise Integration**
- Configure GitLab integration in `config/gitlab_config.py`
- Set up authentication and authorization
- Configure database connections if needed
- Set up monitoring and logging

## 📋 System Requirements

### **Minimum Requirements**
- **OS**: Windows 7+, macOS 10.14+, Ubuntu 18.04+
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 500MB free space
- **Network**: Internet connection for initial setup

### **Recommended Requirements**
- **OS**: Windows 10+, macOS 11+, Ubuntu 20.04+
- **RAM**: 8GB or more
- **Storage**: 1GB free space
- **Network**: Stable internet connection
- **Browser**: Chrome, Firefox, Safari, or Edge (latest versions)

## 🛠️ Troubleshooting

### **Common Issues**

#### **Application Won't Start**
- Check if port 5000 is available
- Ensure firewall allows the application
- Check system requirements
- Try running as administrator (Windows)

#### **Browser Issues**
- Clear browser cache and cookies
- Try a different browser
- Check if JavaScript is enabled
- Ensure popup blockers are disabled

#### **Performance Issues**
- Close other applications to free up memory
- Check available disk space
- Restart the application
- Check system resource usage

### **Getting Help**
- Check the main README.md for detailed documentation
- Review the LICENSE file for usage terms
- The application includes built-in help and documentation
- Visit our GitHub repository for community support

## 🔒 Security Considerations

### **Network Security**
- Configure firewall rules appropriately
- Use HTTPS in production environments
- Set up proper authentication and authorization
- Monitor network traffic and access logs

### **Data Protection**
- Regular backups of configuration and data
- Secure storage of sensitive information
- Access control and user permissions
- Audit trails and logging

## 📞 Support

For technical support and questions:
- **GitHub Issues**: Report bugs and request features
- **Documentation**: Comprehensive guides and tutorials
- **Community**: User forums and discussions
- **Professional Support**: Enterprise support available

---

**CodeCritique** - Professional Code Review Tool  
Version 1.0.0  
Licensed under Apache 2.0 License
