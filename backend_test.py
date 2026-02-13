#!/usr/bin/env python3
"""
VIP Wallet Backend API Testing Suite
Tests all backend APIs according to test_result.md requirements
"""

import requests
import json
import sys
from datetime import datetime

# Test configuration
BASE_URL = "https://sultanat-auth-fix.preview.emergentagent.com/api"
SESSION_TOKEN = "test_session_1768579042684"  # From mongosh command
USER_ID = "user_1768579042684"

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {SESSION_TOKEN}'
        })
        self.results = []
        
    def log_result(self, test_name, success, details="", response_data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if response_data and not success:
            print(f"   Response: {response_data}")
        print()
        
        self.results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'response': response_data
        })
    
    def test_public_apis(self):
        """Test public APIs that don't require authentication"""
        print("=== TESTING PUBLIC APIs ===")
        
        # Test health check
        try:
            response = requests.get(f"{BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "VIP Wallet API" in data["message"]:
                    self.log_result("GET /api/ - Health Check", True, f"Status: {response.status_code}")
                else:
                    self.log_result("GET /api/ - Health Check", False, f"Unexpected response format", data)
            else:
                self.log_result("GET /api/ - Health Check", False, f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /api/ - Health Check", False, f"Request failed: {str(e)}")
        
        # Test VIP levels
        try:
            response = requests.get(f"{BASE_URL}/vip/levels")
            if response.status_code == 200:
                data = response.json()
                if "levels" in data and isinstance(data["levels"], list) and len(data["levels"]) > 0:
                    self.log_result("GET /api/vip/levels - Get VIP Levels", True, f"Found {len(data['levels'])} VIP levels")
                else:
                    self.log_result("GET /api/vip/levels - Get VIP Levels", False, "Invalid response format", data)
            else:
                self.log_result("GET /api/vip/levels - Get VIP Levels", False, f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /api/vip/levels - Get VIP Levels", False, f"Request failed: {str(e)}")
    
    def test_auth_apis(self):
        """Test authentication APIs"""
        print("=== TESTING AUTH APIs ===")
        
        # Test get current user
        try:
            response = self.session.get(f"{BASE_URL}/auth/me")
            if response.status_code == 200:
                data = response.json()
                if "user_id" in data and "email" in data and "name" in data:
                    self.log_result("GET /api/auth/me - Get Current User", True, f"User: {data.get('name')} ({data.get('email')})")
                else:
                    self.log_result("GET /api/auth/me - Get Current User", False, "Missing required user fields", data)
            else:
                self.log_result("GET /api/auth/me - Get Current User", False, f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /api/auth/me - Get Current User", False, f"Request failed: {str(e)}")
        
        # Test logout (but don't actually logout as we need the session for other tests)
        # We'll test this at the end
        pass
    
    def test_wallet_apis(self):
        """Test wallet APIs"""
        print("=== TESTING WALLET APIs ===")
        
        # Test get wallet
        try:
            response = self.session.get(f"{BASE_URL}/wallet")
            if response.status_code == 200:
                data = response.json()
                required_fields = ["user_id", "coins_balance", "stars_balance", "bonus_balance", "withdrawable_balance"]
                if all(field in data for field in required_fields):
                    self.log_result("GET /api/wallet - Get Wallet Balance", True, 
                                  f"Coins: {data['coins_balance']}, Bonus: {data['bonus_balance']}")
                    self.initial_balance = data['coins_balance']
                else:
                    self.log_result("GET /api/wallet - Get Wallet Balance", False, "Missing required wallet fields", data)
            else:
                self.log_result("GET /api/wallet - Get Wallet Balance", False, f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /api/wallet - Get Wallet Balance", False, f"Request failed: {str(e)}")
        
        # Test deposit
        try:
            deposit_amount = 500
            response = self.session.post(f"{BASE_URL}/wallet/deposit", 
                                       json={"amount": deposit_amount})
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "wallet" in data and "transaction_id" in data:
                    new_balance = data["wallet"]["coins_balance"]
                    self.log_result("POST /api/wallet/deposit - Deposit Coins", True, 
                                  f"Deposited {deposit_amount}, New balance: {new_balance}")
                else:
                    self.log_result("POST /api/wallet/deposit - Deposit Coins", False, "Invalid response format", data)
            else:
                self.log_result("POST /api/wallet/deposit - Deposit Coins", False, f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /api/wallet/deposit - Deposit Coins", False, f"Request failed: {str(e)}")
        
        # Test get transactions
        try:
            response = self.session.get(f"{BASE_URL}/wallet/transactions")
            if response.status_code == 200:
                data = response.json()
                if "transactions" in data and "total" in data:
                    self.log_result("GET /api/wallet/transactions - Get Transaction History", True, 
                                  f"Found {len(data['transactions'])} transactions, Total: {data['total']}")
                else:
                    self.log_result("GET /api/wallet/transactions - Get Transaction History", False, "Invalid response format", data)
            else:
                self.log_result("GET /api/wallet/transactions - Get Transaction History", False, f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /api/wallet/transactions - Get Transaction History", False, f"Request failed: {str(e)}")
    
    def test_vip_apis(self):
        """Test VIP APIs"""
        print("=== TESTING VIP APIs ===")
        
        # Test get VIP status
        try:
            response = self.session.get(f"{BASE_URL}/vip/status")
            if response.status_code == 200:
                data = response.json()
                required_fields = ["user_id", "vip_level", "total_recharged", "is_active"]
                if all(field in data for field in required_fields):
                    self.log_result("GET /api/vip/status - Get VIP Status", True, 
                                  f"Level: {data['vip_level']}, Active: {data['is_active']}, Recharged: {data['total_recharged']}")
                    self.vip_level = data['vip_level']
                    self.total_recharged = data['total_recharged']
                else:
                    self.log_result("GET /api/vip/status - Get VIP Status", False, "Missing required VIP fields", data)
            else:
                self.log_result("GET /api/vip/status - Get VIP Status", False, f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /api/vip/status - Get VIP Status", False, f"Request failed: {str(e)}")
        
        # Test VIP subscription - try level 1 (Bronze)
        try:
            vip_level = 1
            response = self.session.post(f"{BASE_URL}/vip/subscribe", 
                                       json={"level": vip_level})
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "vip_status" in data and "transaction_id" in data:
                    self.log_result("POST /api/vip/subscribe - Subscribe to VIP", True, 
                                  f"Subscribed to level {vip_level}, Transaction: {data['transaction_id']}")
                else:
                    self.log_result("POST /api/vip/subscribe - Subscribe to VIP", False, "Invalid response format", data)
            elif response.status_code == 400:
                # This might be expected if user doesn't meet requirements
                error_msg = response.json().get("detail", "Unknown error")
                if "recharge" in error_msg.lower() or "balance" in error_msg.lower():
                    self.log_result("POST /api/vip/subscribe - Subscribe to VIP", True, 
                                  f"Expected error (insufficient requirements): {error_msg}")
                else:
                    self.log_result("POST /api/vip/subscribe - Subscribe to VIP", False, f"Unexpected error: {error_msg}")
            else:
                self.log_result("POST /api/vip/subscribe - Subscribe to VIP", False, f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /api/vip/subscribe - Subscribe to VIP", False, f"Request failed: {str(e)}")
    
    def test_notifications_api(self):
        """Test notifications API"""
        print("=== TESTING NOTIFICATIONS API ===")
        
        try:
            response = self.session.get(f"{BASE_URL}/notifications")
            if response.status_code == 200:
                data = response.json()
                if "notifications" in data and "unread_count" in data:
                    self.log_result("GET /api/notifications - Get Notifications", True, 
                                  f"Found {len(data['notifications'])} notifications, Unread: {data['unread_count']}")
                else:
                    self.log_result("GET /api/notifications - Get Notifications", False, "Invalid response format", data)
            else:
                self.log_result("GET /api/notifications - Get Notifications", False, f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GET /api/notifications - Get Notifications", False, f"Request failed: {str(e)}")
    
    def test_logout(self):
        """Test logout API - do this last"""
        print("=== TESTING LOGOUT ===")
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/logout")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_result("POST /api/auth/logout - Logout", True, "Successfully logged out")
                else:
                    self.log_result("POST /api/auth/logout - Logout", False, "Logout failed", data)
            else:
                self.log_result("POST /api/auth/logout - Logout", False, f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("POST /api/auth/logout - Logout", False, f"Request failed: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests in order"""
        print(f"Starting VIP Wallet Backend API Tests")
        print(f"Base URL: {BASE_URL}")
        print(f"Session Token: {SESSION_TOKEN[:20]}...")
        print(f"Test Time: {datetime.now().isoformat()}")
        print("=" * 60)
        
        # Run tests in logical order
        self.test_public_apis()
        self.test_auth_apis()
        self.test_wallet_apis()
        self.test_vip_apis()
        self.test_notifications_api()
        self.test_logout()
        
        # Summary
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r['success'])
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\nFAILED TESTS:")
            for result in self.results:
                if not result['success']:
                    print(f"  ❌ {result['test']}: {result['details']}")
        
        return passed == total

if __name__ == "__main__":
    tester = APITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)