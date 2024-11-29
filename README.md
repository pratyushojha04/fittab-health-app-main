# FitTab - Fitness Tracking and Workout Analysis Application

FitTab is a comprehensive web application built with Flask that helps users track their workouts, analyze exercise form using computer vision, and maintain their fitness journey. The application includes features like real-time pose detection, workout tracking, PDF report generation, and user profile management.

## Features

- 🏋️‍♂️ Real-time pose detection for exercise form analysis
- 📊 Workout tracking and progress monitoring
- 📱 User profile management
- 📄 PDF report generation for workout history
- 🗺️ Nearby gym locator
- 📈 Exercise statistics and analytics
- 🔐 Secure user authentication
- 📸 Profile picture upload functionality

## Prerequisites

- Python 3.7+
- OpenCV
- Flask
- SQLite3
- Mediapipe
- Modern web browser with WebRTC support

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd fittab-new
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
flask db upgrade
```

## Project Structure

```
fittab-new/
├── app.py                 # Main application file
├── helper.py             # Helper functions
├── dumbel_curl_script.py # Pose detection implementation
├── requirements.txt      # Project dependencies
├── static/              # Static files (CSS, JS, images)
├── templates/           # HTML templates
├── migrations/          # Database migrations
└── instance/           # Instance-specific files
```

## Configuration

The application uses the following configuration settings in `app.py`:

- `SQLALCHEMY_DATABASE_URI`: SQLite database location
- `SECRET_KEY`: Application secret key for session management
- `UPLOAD_FOLDER`: Location for uploaded files
- `MAX_CONTENT_LENGTH`: Maximum file upload size (16MB)
- `SESSION_COOKIE_HTTPONLY`: Security setting for session cookies
- `SESSION_COOKIE_SECURE`: HTTPS-only cookie setting

## Running the Application

1. Start the Flask development server:
```bash
python app.py
```

2. Access the application at: `http://localhost:5001`

## Technical Architecture

### Backend Architecture
- **Flask Framework**: Core web framework handling routing and request processing
- **SQLAlchemy ORM**: Database abstraction layer for user and workout data management
- **Flask-Migrate**: Database migration management
- **Flask-SocketIO**: WebSocket implementation for real-time video streaming
- **Werkzeug**: WSGI web application library for security and utilities

### Frontend Components
- **HTML5/CSS3**: Modern, responsive user interface
- **JavaScript**: Client-side interactivity and WebSocket communication
- **WebRTC**: Real-time video streaming capabilities
- **Canvas API**: Real-time drawing of pose detection results

### Computer Vision Pipeline
- **OpenCV**: Image processing and frame manipulation
- **MediaPipe**: Advanced pose detection and landmark tracking
- **NumPy**: Mathematical computations for pose analysis

## Detailed Features

### 1. Pose Detection System
The application uses a sophisticated pose detection system implemented in `dumbel_curl_script.py`:
- Real-time landmark detection for 33 body points
- Angle calculation between joints for form analysis
- Rep counting based on angle thresholds
- Visual feedback with on-screen metrics
- Customizable detection confidence thresholds

### 2. User Management System
Comprehensive user profile management:
- **Registration**:
  - Email validation
  - Secure password hashing
  - Profile picture upload with size validation
  - Basic fitness metrics collection
- **Profile Management**:
  - Height, weight, and age tracking
  - Progress photo management
  - Workout history visualization
  - Personal records tracking

### 3. Workout Tracking System
Detailed workout logging and analysis:
- **Exercise Logging**:
  - Set-by-set tracking
  - Weight and rep recording
  - Rest time monitoring
  - Form quality notes
- **Progress Tracking**:
  - Weight progression graphs
  - Volume calculations
  - Personal records tracking
  - Performance analytics

### 4. Report Generation
Sophisticated PDF report generation using ReportLab:
- **Workout Summaries**:
  - Exercise breakdown
  - Set and rep analysis
  - Weight progression
  - Form improvement notes
- **Progress Reports**:
  - Monthly/weekly summaries
  - Performance metrics
  - Goal tracking
  - Comparison charts

## Development Setup

### Environment Setup
1. System Requirements:
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install python3-pip python3-venv libsqlite3-dev python3-opencv
   ```

2. Python Virtual Environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   ```

3. Install Dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Database Setup
1. Initialize the database:
   ```bash
   flask db init
   ```

2. Create and apply migrations:
   ```bash
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

### Configuration
1. Environment Variables:
   ```bash
   export FLASK_APP=app.py
   export FLASK_ENV=development
   export SECRET_KEY=your_secret_key
   ```

2. Application Configuration:
   ```python
   # config.py
   class Config:
       SQLALCHEMY_TRACK_MODIFICATIONS = False
       SQLALCHEMY_DATABASE_URI = 'sqlite:///users.sqlite3'
       MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
       UPLOAD_FOLDER = 'static/uploads'
   ```

## API Documentation

### Authentication Endpoints
- `POST /login`: User authentication
  ```json
  {
    "email": "user@example.com",
    "password": "secure_password"
  }
  ```
- `POST /register`: New user registration
  ```json
  {
    "name": "John Doe",
    "email": "user@example.com",
    "password": "secure_password",
    "age": 25,
    "height": 175,
    "weight": 70
  }
  ```

### Workout Endpoints
- `POST /workouts`: Log new workout
- `GET /workouts`: Retrieve workout history
- `GET /workouts/download`: Download workout data
- `GET /workouts/report`: Generate PDF report

### Profile Endpoints
- `GET /profile`: Get user profile
- `PUT /profile`: Update user information
- `POST /profile/picture`: Upload profile picture

## Performance Optimization

### Video Processing
- Frame rate optimization
- Resolution scaling
- Parallel processing for pose detection
- Memory management for video streams

### Database Optimization
- Indexed queries
- Efficient relationship mapping
- Lazy loading of related data
- Connection pooling

### Caching Strategy
- Static asset caching
- Session data caching
- Database query results caching
- API response caching

## Security Measures

### Authentication Security
- Bcrypt password hashing
- Session management
- CSRF protection
- Rate limiting

### Data Security
- Input validation
- SQL injection prevention
- XSS protection
- File upload validation

### Network Security
- HTTPS enforcement
- Secure WebSocket connections
- Header security
- Cookie security

## Testing

### Unit Tests
```bash
python -m pytest tests/unit/
```

### Integration Tests
```bash
python -m pytest tests/integration/
```

### Performance Tests
```bash
python -m pytest tests/performance/
```

## Deployment

### Production Setup
1. Gunicorn Configuration:
   ```bash
   gunicorn --worker-class eventlet -w 1 app:app
   ```

2. Nginx Configuration:
   ```nginx
   location / {
       proxy_pass http://localhost:8000;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection 'upgrade';
       proxy_set_header Host $host;
   }
   ```

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "app:app"]
```

## Monitoring and Logging

### Application Monitoring
- Error tracking
- Performance metrics
- User activity logging
- System health checks

### Log Management
- Application logs
- Access logs
- Error logs
- Security logs

## Features in Detail

### User Management
- User registration with profile information
- Secure password hashing
- Profile picture upload
- Personal information management

### Workout Tracking
- Record exercises, sets, reps, and weights
- Track workout history
- Generate PDF reports of workout data
- Export workout data to CSV

### Real-time Pose Detection
- Live camera feed for exercise form analysis
- Real-time pose detection using MediaPipe
- Exercise form feedback
- WebSocket integration for smooth streaming

### Reporting
- Generate detailed PDF reports
- Export workout history
- View progress statistics
- Analyze workout trends

## Dependencies

Main dependencies include:
- Flask - Web framework
- OpenCV - Computer vision library
- MediaPipe - Pose detection
- SQLAlchemy - Database ORM
- ReportLab - PDF generation
- Flask-SocketIO - Real-time communication
- Werkzeug - WSGI utilities

## Security Features

- Password hashing using Werkzeug security
- Secure session management
- HTTPS cookie settings
- File upload validation
- SQL injection prevention through SQLAlchemy

## Error Handling

The application includes error handling for:
- File upload errors
- Authentication failures
- Database connection issues
- WebSocket connection problems
- Invalid form submissions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the terms of the LICENSE file included in the repository.

## Troubleshooting

### Common Issues

1. TLS Handshake Timeout
   - Check your internet connection
   - Verify SSL/TLS configuration
   - Ensure proper proxy settings if behind a corporate network

2. Database Errors
   - Ensure SQLite is properly installed
   - Check database file permissions
   - Run database migrations

3. Camera Access Issues
   - Grant camera permissions in browser
   - Check if camera is being used by another application
   - Verify WebRTC support in browser

### Support

For support, please:
1. Check the existing issues in the repository
2. Create a new issue with detailed information about your problem
3. Include relevant error messages and screenshots

## Acknowledgments

- OpenCV for computer vision capabilities
- MediaPipe for pose detection
- Flask community for the excellent web framework
- All contributors to the project
