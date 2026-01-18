# 📁 GYAN SULTANAT - SOURCE CODE STRUCTURE

## Backend (/app/backend/)
```
/app/backend/
├── server.py          # Main FastAPI server (8500+ lines)
├── requirements.txt   # Python dependencies
└── .env              # Environment variables
```

### Key Backend Features:
- FastAPI framework
- MongoDB (Motor async driver)
- OpenAI GPT-4o-mini integration
- JWT Authentication
- QR Code generation
- PDF generation (ReportLab)
- Digital signature system

## Frontend (/app/frontend/)
```
/app/frontend/
├── app/
│   ├── (tabs)/
│   │   ├── _layout.tsx
│   │   ├── home.tsx
│   │   ├── education.tsx
│   │   ├── profile.tsx
│   │   ├── vip.tsx
│   │   ├── ai-teacher.tsx
│   │   ├── leaderboard.tsx
│   │   └── talent-register.tsx
│   ├── _layout.tsx
│   ├── index.tsx
│   ├── login.tsx
│   └── onboarding.tsx
├── assets/
│   └── playstore/
│       ├── PRIVACY_POLICY.html
│       ├── PLAY_STORE_DESCRIPTION.md
│       ├── PUBLIC_RELEASE_CHECKLIST.md
│       └── RELEASE_NOTES.txt
├── src/
│   ├── components/
│   └── utils/
├── app.json
├── eas.json
└── package.json
```

### Key Frontend Technologies:
- React Native
- Expo SDK 53
- Expo Router
- TypeScript
- React Navigation

## Configuration Files
```
eas.json          # EAS Build configuration
app.json          # Expo app configuration
package.json      # Node dependencies
tsconfig.json     # TypeScript configuration
```

## API Endpoints (Backend)
Total: 50+ endpoints

### Core APIs:
- /api/health
- /api/auth/*
- /api/wallet/*
- /api/vip/*

### Payment APIs:
- /api/payment/*
- /api/sultan/*
- /api/finance/*

### Muqaddas Network APIs:
- /api/muqaddas/*
- /api/seal/*
- /api/qr/*

### Legal APIs:
- /api/legal/*
- /api/digital-signature/*
