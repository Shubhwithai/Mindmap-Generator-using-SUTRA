import requests
import unittest
import json
import time
import os
from datetime import datetime

class FlashCardAPITester:
    def __init__(self, base_url="https://81f1f07a-1c4b-4613-9ec0-b6fc3c391a6d.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        # Using the provided API key for testing
        self.sutra_api_key = "sutra_j6OBb2v3MIAoiyhhVE7h8W3xW0NhNN3J1CicKrLCLVaocxb0feQpGXQWq16t"
        self.test_deck_ids = []

    def run_test(self, name, method, endpoint, expected_status, data=None, is_file_download=False):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if is_file_download:
                    response = requests.post(url, json=data, headers=headers, stream=True)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                
                if is_file_download:
                    # For file downloads, return the raw response
                    return success, response
                else:
                    try:
                        return success, response.json()
                    except:
                        return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"Response: {response.json()}")
                except:
                    print(f"Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test("Root Endpoint", "GET", "", 200)

    def test_sutra_api_connection(self):
        """Test the Sutra API connection"""
        return self.run_test(
            "Sutra API Connection", 
            "POST", 
            "test-sutra", 
            200, 
            data={"api_key": self.sutra_api_key}
        )

    def test_generate_cards(self, topic="Mars", language="english", count=3):
        """Test generating flash cards"""
        return self.run_test(
            f"Generate Cards ({topic} in {language})", 
            "POST", 
            "generate-cards", 
            200, 
            data={
                "topic": topic,
                "language": language,
                "count": count,
                "sutra_api_key": self.sutra_api_key
            }
        )

    def test_get_all_decks(self):
        """Test getting all decks"""
        return self.run_test("Get All Decks", "GET", "decks", 200)

    def test_get_deck_by_id(self, deck_id):
        """Test getting a specific deck by ID"""
        return self.run_test(f"Get Deck by ID ({deck_id})", "GET", f"decks/{deck_id}", 200)

    def test_delete_deck(self, deck_id):
        """Test deleting a deck"""
        return self.run_test(f"Delete Deck ({deck_id})", "DELETE", f"decks/{deck_id}", 200)
    
    def test_export_decks(self, deck_ids=None, export_format="json"):
        """Test exporting decks in various formats"""
        data = {
            "deck_ids": deck_ids if deck_ids else [],
            "format": export_format
        }
        
        return self.run_test(
            f"Export Decks ({export_format.upper()})", 
            "POST", 
            "export", 
            200, 
            data=data,
            is_file_download=True
        )
    
    def save_export_file(self, response, export_format):
        """Save the exported file to disk"""
        filename = f"test_export.{export_format}"
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        
        print(f"✅ Saved export file to {filename}")
        return os.path.exists(filename) and os.path.getsize(filename) > 0

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Flash Card API Tests")
        print(f"Base URL: {self.base_url}")
        print("=" * 50)

        # Test root endpoint
        self.test_root_endpoint()

        # Test Sutra API connection
        success, response = self.test_sutra_api_connection()
        if success:
            print(f"Sutra API Test Response: {response.get('test_response', 'No response')}")

        # Test generating cards in different languages including new Gujarati and Marathi
        languages_to_test = ["english", "hindi", "gujarati", "marathi"]
        topics_to_test = {
            "english": "Solar System",
            "hindi": "Cooking",
            "gujarati": "Family",
            "marathi": "Education"
        }
        
        for language in languages_to_test:
            topic = topics_to_test.get(language, "General Knowledge")
            success, response = self.test_generate_cards(topic, language)
            if success and response.get('success'):
                deck_id = response.get('deck', {}).get('id')
                if deck_id:
                    self.test_deck_ids.append(deck_id)
                    print(f"Created deck ID: {deck_id}")
                    
                    # Test getting the deck by ID
                    self.test_get_deck_by_id(deck_id)
            
            # Add a small delay to avoid rate limiting
            time.sleep(1)

        # Test getting all decks
        success, response = self.test_get_all_decks()
        if success:
            print(f"Found {len(response)} decks")
        
        # Test export functionality with all formats
        if self.test_deck_ids:
            # Test exporting specific decks in JSON format
            success, response = self.test_export_decks(self.test_deck_ids[:2], "json")
            if success:
                self.save_export_file(response, "json")
            
            # Test exporting specific decks in CSV format
            success, response = self.test_export_decks(self.test_deck_ids[:2], "csv")
            if success:
                self.save_export_file(response, "csv")
            
            # Test exporting specific decks in PDF format
            success, response = self.test_export_decks(self.test_deck_ids[:2], "pdf")
            if success:
                self.save_export_file(response, "pdf")
            
            # Test exporting all decks (empty deck_ids)
            success, response = self.test_export_decks(None, "json")
            if success:
                print("✅ Successfully exported all decks")

        # Test deleting decks
        for deck_id in self.test_deck_ids:
            self.test_delete_deck(deck_id)

        # Final test to verify decks were deleted
        success, response = self.test_get_all_decks()
        if success:
            remaining_test_decks = [deck for deck in response if deck.get('id') in self.test_deck_ids]
            if remaining_test_decks:
                print(f"❌ Warning: {len(remaining_test_decks)} test decks were not properly deleted")
            else:
                print("✅ All test decks were successfully deleted")

        # Print test summary
        print("\n" + "=" * 50)
        print(f"📊 Tests passed: {self.tests_passed}/{self.tests_run}")
        print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.2f}%")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = FlashCardAPITester()
    tester.run_all_tests()
