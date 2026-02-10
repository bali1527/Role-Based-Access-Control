# 📄 RBAC PDF Management System

A modern, role-based PDF management system built with **FastAPI** and **JavaScript**, featuring professional UI design and comprehensive permission controls.

## 🎯 Features

### ✨ Core Features
- **Role-Based Access Control** - Three roles with different permissions
- **PDF Management** - Upload, Read, Update, and Delete PDFs
- **Modern UI** - Professional gradient design with animations
- **Responsive Design** - Works seamlessly on desktop, tablet, and mobile
- **Real-time Permissions** - Dynamic button visibility based on user role
- **User Profile Display** - Top-right corner shows username and role
- **Uploader Information** - Each PDF shows who uploaded it and their role

### 🔐 Permission Levels

| Permission | User | Admin | Super Admin |
|-----------|:----:|:-----:|:----------:|
| **Read PDFs** | ✅ | ✅ | ✅ |
| **Create PDFs** | ❌ | ✅ | ✅ |
| **Update PDFs** | ❌ | ✅ | ✅ |
| **Delete PDFs** | ❌ | ❌ | ✅ |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Virtual environment activated
- Dependencies installed (`requirements.txt`)

### Running the Server

```bash
cd c:\Users\User\Desktop\RBAC
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Access the Application
Open your browser: **`http://127.0.0.1:8000`**

---

## 👤 Demo Accounts

### User (Read-Only)
```
Username: user1
Password: user123
```

### Admin (Create, Read, Update)
```
Username: admin1
Password: admin123
```

### Super Admin (Full Access)
```
Username: superadmin1
Password: super123
```

---

## 📁 Project Structure

```
RBAC/
├── main.py                    # FastAPI application & routes
├── requirements.txt           # Python dependencies
├── check_db.py               # Database inspection tool
│
├── app/
│   ├── __init__.py
│   ├── auth.py               # JWT authentication
│   ├── database.py           # SQLAlchemy setup
│   ├── deps.py               # Dependency injection
│   ├── models.py             # Database models
│   ├── schemas.py            # Pydantic schemas
│   └── pdfs.py               # PDF management endpoints
│
├── frontend/
│   ├── index.html            # Login page
│   ├── dashboard.html        # Dashboard
│   ├── app.js                # Frontend JavaScript
│   ├── style.css             # Modern styling
│   └── rbac.db               # SQLite database
│
├── uploads/
│   └── pdfs/                 # PDF storage directory
│
├── CHANGES_SUMMARY.md        # Detailed change log
└── TESTING_GUIDE.md          # Testing procedures
```

---

## 🔧 API Endpoints

### Authentication
- `POST /login` - Login and get JWT token
- `POST /users` - Create new user account

### User Management
- `GET /users/me` - Get current user info
- `GET /users/me/permissions` - Get user permissions

### PDF Management
- `POST /api/pdf/upload` - Upload new PDF (Requires CREATE)
- `GET /api/pdf/` - List all PDFs (Requires READ)
- `GET /api/pdf/{id}` - Get PDF metadata (Requires READ)
- `PUT /api/pdf/{id}` - Update PDF title (Requires UPDATE)
- `DELETE /api/pdf/{id}` - Delete PDF (Requires DELETE)
- `GET /api/pdf/{id}/download` - Download PDF file (Requires READ)

### System
- `GET /health` - Health check
- `POST /init` - Initialize database with demo data

---

## 🎨 UI Highlights

### Navigation Bar
- User avatar and name display
- Current role badge
- Quick logout button
- Responsive on all screen sizes

### Upload Section
- Title input field
- PDF file selector
- Real-time validation
- Success/error feedback

### PDF Grid
- Responsive multi-column layout
- PDF card with metadata
- Uploader role badge
- Permission-based action buttons
- Smooth hover animations

### Action Buttons
- 📥 **Read** - Download/view PDF (All users with READ)
- ✏️ **Edit** - Update title (Admin & Super Admin with UPDATE)
- 🗑️ **Delete** - Remove PDF (Super Admin only with DELETE)

---

## 🔐 Security Features

- ✅ JWT-based authentication
- ✅ Password hashing with bcrypt
- ✅ Role-based access control (RBAC)
- ✅ XSS prevention (HTML escaping)
- ✅ CORS configuration
- ✅ Secure file storage

---

## 📱 Responsive Breakpoints

- **Desktop**: 1200px+ (Multi-column grid)
- **Tablet**: 768px - 1199px (2-3 columns)
- **Mobile**: 320px - 767px (Single column)

---

## 🌈 Design System

### Color Palette
- **Primary**: #667eea (Blue)
- **Secondary**: #764ba2 (Purple)
- **Success**: #48bb78 (Green)
- **Danger**: #f56565 (Red)
- **Warning**: #ed8936 (Orange)

### Typography
- Font: System UI, Segoe UI, Roboto
- Headings: Bold weights
- Body: Regular weights

### Spacing & Layout
- Consistent padding/margins
- Flexbox & CSS Grid layout
- Smooth transitions (300ms)
- Box shadows for depth

---

## 🧪 Testing

### Quick Test
1. Open `http://127.0.0.1:8000`
2. Login with `user1 / user123`
3. Try viewing PDFs (should work)
4. Try uploading PDF (button should be hidden)
5. Logout and login as `admin1 / admin123`
6. Try uploading and editing PDFs

### Full Testing
See [TESTING_GUIDE.md](TESTING_GUIDE.md) for comprehensive testing procedures.

---

## 📚 Database

### Tables
- `users` - User accounts
- `roles` - Role definitions
- `permissions` - Permission definitions
- `user_roles` - User-role mapping (M:M)
- `role_permissions` - Role-permission mapping (M:M)
- `pdfs` - PDF metadata

### Database File
- **Location**: `uploads/pdfs/` folder
- **Type**: SQLite (default)
- **Config**: `DATABASE_URL` environment variable

---

## 🚨 Troubleshooting

### Server won't start
```bash
# Verify port 8000 is available
netstat -ano | findstr :8000

# Kill process on port 8000 if needed
taskkill /PID <PID> /F
```

### Static files not loading
- Verify `frontend/` folder exists
- Check file paths in main.py
- Clear browser cache (Ctrl+Shift+R)

### Login fails
- Run `http://127.0.0.1:8000/init` to reset database
- Check credentials in demo accounts section

### Permission denied errors
- Verify user role and permissions
- Check role assignments in database
- Reload page to refresh permissions

---

## 📝 Recent Changes

### Version 1.1.0
- ✨ Added PDF edit (UPDATE) functionality
- ✨ Enhanced modern UI with gradients and animations
- ✨ Added uploader role display on PDF cards
- ✨ Improved top-right user profile section
- 🐛 Fixed permission assignments (Admin no longer has DELETE)
- 🐛 Fixed file path resolution for static files
- 🐛 Enhanced error handling and user feedback

See [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md) for detailed changes.

---

## 📞 Support

For issues or questions:
1. Check [TESTING_GUIDE.md](TESTING_GUIDE.md) for common issues
2. Review [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md) for implementation details
3. Check browser console (F12) for errors
4. Verify server logs in terminal

---

## 📄 License

This project is provided as-is for educational purposes.

---

## 🎉 What's Working

✅ User authentication with roles
✅ PDF upload with role restrictions
✅ PDF listing with metadata
✅ PDF reading/downloading
✅ PDF title editing (Admin+)
✅ PDF deletion (Super Admin only)
✅ Modern responsive UI
✅ Permission-based button visibility
✅ User profile display
✅ Real-time role badges
✅ Smooth animations
✅ Mobile responsiveness
✅ Error handling
✅ Success feedback

---

**Ready to use! 🚀 Open http://127.0.0.1:8000 in your browser.**
