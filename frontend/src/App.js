import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const FlashCard = ({ card, isFlipped, onFlip }) => {
  return (
    <div 
      className="flash-card w-full h-64 cursor-pointer perspective-1000"
      onClick={onFlip}
    >
      <div className={`card-inner w-full h-full relative transform-style-preserve-3d transition-transform duration-700 ${isFlipped ? 'rotate-y-180' : ''}`}>
        <div className="card-face card-front absolute w-full h-full backface-hidden bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl shadow-lg flex items-center justify-center p-6">
          <p className="text-white text-xl font-semibold text-center">{card.front}</p>
        </div>
        <div className="card-face card-back absolute w-full h-full backface-hidden bg-gradient-to-br from-green-500 to-teal-600 rounded-xl shadow-lg flex items-center justify-center p-6 rotate-y-180">
          <p className="text-white text-lg text-center">{card.back}</p>
        </div>
      </div>
    </div>
  );
};

const LanguageSelector = ({ selected, onChange }) => {
  const languages = [
    { code: 'english', name: 'English', flag: '🇺🇸' },
    { code: 'hindi', name: 'हिंदी', flag: '🇮🇳' },
    { code: 'gujarati', name: 'ગુજરાતી', flag: '🇮🇳' },
    { code: 'marathi', name: 'मराठी', flag: '🇮🇳' },
    { code: 'spanish', name: 'Español', flag: '🇪🇸' },
    { code: 'french', name: 'Français', flag: '🇫🇷' },
    { code: 'german', name: 'Deutsch', flag: '🇩🇪' },
    { code: 'chinese', name: '中文', flag: '🇨🇳' },
    { code: 'japanese', name: '日本語', flag: '🇯🇵' },
    { code: 'arabic', name: 'العربية', flag: '🇸🇦' }
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
      {languages.map((lang) => (
        <button
          key={lang.code}
          onClick={() => onChange(lang.code)}
          className={`p-3 rounded-lg border-2 transition-all flex items-center justify-center space-x-2 ${
            selected === lang.code
              ? 'border-blue-500 bg-blue-50 text-blue-700'
              : 'border-gray-200 hover:border-gray-300 bg-white'
          }`}
        >
          <span className="text-lg">{lang.flag}</span>
          <span className="text-sm font-medium">{lang.name}</span>
        </button>
      ))}
    </div>
  );
};

const ExportModal = ({ isOpen, onClose, decks, onExport }) => {
  const [selectedDecks, setSelectedDecks] = useState([]);
  const [exportFormat, setExportFormat] = useState('json');
  const [selectAll, setSelectAll] = useState(false);

  useEffect(() => {
    if (selectAll) {
      setSelectedDecks(decks.map(deck => deck.id));
    } else {
      setSelectedDecks([]);
    }
  }, [selectAll, decks]);

  const handleDeckToggle = (deckId) => {
    setSelectedDecks(prev => 
      prev.includes(deckId) 
        ? prev.filter(id => id !== deckId)
        : [...prev, deckId]
    );
  };

  const handleExport = () => {
    onExport(selectedDecks, exportFormat);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl p-6 max-w-md w-full mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-800">📁 Export Flash Cards</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            ✕
          </button>
        </div>

        <div className="space-y-4">
          {/* Format Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Export Format</label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { value: 'json', label: '📄 JSON', desc: 'For backup' },
                { value: 'csv', label: '📊 CSV', desc: 'For Excel' },
                { value: 'pdf', label: '📋 PDF', desc: 'For printing' }
              ].map(format => (
                <button
                  key={format.value}
                  onClick={() => setExportFormat(format.value)}
                  className={`p-3 text-center rounded-lg border-2 transition-all ${
                    exportFormat === format.value
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="text-sm font-medium">{format.label}</div>
                  <div className="text-xs text-gray-500">{format.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Deck Selection */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-gray-700">Select Decks</label>
              <button
                onClick={() => setSelectAll(!selectAll)}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                {selectAll ? 'Deselect All' : 'Select All'}
              </button>
            </div>
            
            <div className="max-h-48 overflow-y-auto border border-gray-200 rounded-lg">
              {decks.length === 0 ? (
                <p className="p-4 text-gray-500 text-center">No decks available</p>
              ) : (
                decks.map(deck => (
                  <div key={deck.id} className="flex items-center p-3 border-b border-gray-100 last:border-b-0">
                    <input
                      type="checkbox"
                      checked={selectedDecks.includes(deck.id)}
                      onChange={() => handleDeckToggle(deck.id)}
                      className="mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">{deck.name}</div>
                      <div className="text-xs text-gray-500">{deck.cards.length} cards • {deck.language}</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Export Button */}
          <div className="flex gap-3 pt-2">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleExport}
              disabled={selectedDecks.length === 0 && exportFormat !== 'json'}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Export {selectedDecks.length > 0 ? `(${selectedDecks.length})` : 'All'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

function App() {
  const [apiKey, setApiKey] = useState(localStorage.getItem('sutra_api_key') || '');
  const [topic, setTopic] = useState('');
  const [language, setLanguage] = useState('english');
  const [cardCount, setCardCount] = useState(5);
  const [loading, setLoading] = useState(false);
  const [currentDeck, setCurrentDeck] = useState(null);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isCardFlipped, setIsCardFlipped] = useState(false);
  const [allDecks, setAllDecks] = useState([]);
  const [showDecks, setShowDecks] = useState(false);
  const [testingApi, setTestingApi] = useState(false);
  const [apiStatus, setApiStatus] = useState(null);
  const [showExportModal, setShowExportModal] = useState(false);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    loadDecks();
  }, []);

  useEffect(() => {
    if (apiKey) {
      localStorage.setItem('sutra_api_key', apiKey);
    }
  }, [apiKey]);

  const testSutraAPI = async () => {
    if (!apiKey.trim()) {
      setApiStatus({ success: false, message: 'Please enter your Sutra API key' });
      return;
    }

    setTestingApi(true);
    try {
      const response = await axios.post(`${API}/test-sutra`, {
        api_key: apiKey
      });
      setApiStatus(response.data);
    } catch (error) {
      setApiStatus({
        success: false,
        message: `Connection failed: ${error.response?.data?.detail || error.message}`
      });
    }
    setTestingApi(false);
  };

  const generateCards = async () => {
    if (!apiKey.trim()) {
      alert('Please enter your Sutra API key');
      return;
    }
    if (!topic.trim()) {
      alert('Please enter a topic');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/generate-cards`, {
        topic: topic,
        language: language,
        count: cardCount,
        sutra_api_key: apiKey
      });

      if (response.data.success) {
        setCurrentDeck(response.data.deck);
        setCurrentCardIndex(0);
        setIsCardFlipped(false);
        loadDecks(); // Refresh deck list
      } else {
        alert('Failed to generate cards: ' + response.data.message);
      }
    } catch (error) {
      alert('Error generating cards: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  const loadDecks = async () => {
    try {
      const response = await axios.get(`${API}/decks`);
      setAllDecks(response.data);
    } catch (error) {
      console.error('Error loading decks:', error);
    }
  };

  const selectDeck = (deck) => {
    setCurrentDeck(deck);
    setCurrentCardIndex(0);
    setIsCardFlipped(false);
    setShowDecks(false);
  };

  const deleteDeck = async (deckId) => {
    if (window.confirm('Are you sure you want to delete this deck?')) {
      try {
        await axios.delete(`${API}/decks/${deckId}`);
        loadDecks();
        if (currentDeck && currentDeck.id === deckId) {
          setCurrentDeck(null);
        }
      } catch (error) {
        alert('Error deleting deck: ' + error.message);
      }
    }
  };

  const exportDecks = async (selectedDeckIds, format) => {
    setExporting(true);
    try {
      const response = await axios.post(`${API}/export`, {
        deck_ids: selectedDeckIds,
        format: format
      }, {
        responseType: 'blob' // Important for file downloads
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Set filename based on format
      const timestamp = new Date().toISOString().slice(0, 19).replace(/[:]/g, '-');
      const extension = format === 'json' ? 'json' : format === 'csv' ? 'csv' : 'pdf';
      link.setAttribute('download', `flashcards_export_${timestamp}.${extension}`);
      
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      alert(`Successfully exported ${selectedDeckIds.length || allDecks.length} deck(s) as ${format.toUpperCase()}`);
    } catch (error) {
      alert('Export failed: ' + (error.response?.data?.detail || error.message));
    }
    setExporting(false);
  };

  const nextCard = () => {
    if (currentDeck && currentCardIndex < currentDeck.cards.length - 1) {
      setCurrentCardIndex(currentCardIndex + 1);
      setIsCardFlipped(false);
    }
  };

  const prevCard = () => {
    if (currentCardIndex > 0) {
      setCurrentCardIndex(currentCardIndex - 1);
      setIsCardFlipped(false);
    }
  };

  const flipCard = () => {
    setIsCardFlipped(!isCardFlipped);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-white to-cyan-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            GENERATE FLASH CARDS USING SUTRA
          </h1>
          <p className="text-gray-600">🌍 Multilingual AI-powered learning</p>
          <p className="text-gray-500 text-sm">Create educational flash cards in any language</p>
        </div>

        {/* API Key Section */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">🔑 Sutra API Configuration</h2>
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sutra API Key
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your Sutra API key"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <button
              onClick={testSutraAPI}
              disabled={testingApi}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {testingApi ? 'Testing...' : 'Test API'}
            </button>
          </div>
          
          {apiStatus && (
            <div className={`mt-4 p-3 rounded-lg ${apiStatus.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
              <p className="font-medium">{apiStatus.success ? '✅' : '❌'} {apiStatus.message}</p>
              {apiStatus.test_response && (
                <p className="text-sm mt-1">Test response: {apiStatus.test_response}</p>
              )}
            </div>
          )}
        </div>

        {/* Generation Form */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">📚 Generate New Cards</h2>
          
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Topic
              </label>
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g., Mars, Cooking, Business Terms, History"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Language
              </label>
              <LanguageSelector selected={language} onChange={setLanguage} />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Number of Cards
              </label>
              <select
                value={cardCount}
                onChange={(e) => setCardCount(parseInt(e.target.value))}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value={3}>3 cards</option>
                <option value={5}>5 cards</option>
                <option value={8}>8 cards</option>
                <option value={10}>10 cards</option>
              </select>
            </div>

            <button
              onClick={generateCards}
              disabled={loading || !apiKey.trim()}
              className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 transition-all transform hover:scale-105"
            >
              {loading ? '🎯 Generating Cards...' : '✨ Generate Flash Cards'}
            </button>
          </div>
        </div>

        {/* Deck Management */}
        <div className="flex gap-4 mb-8">
          <button
            onClick={() => setShowDecks(!showDecks)}
            className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            📋 My Decks ({allDecks.length})
          </button>
          
          <button
            onClick={() => setShowExportModal(true)}
            disabled={allDecks.length === 0}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
          >
            📁 Export Decks
          </button>
        </div>

        {/* Deck List */}
        {showDecks && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">📚 Saved Decks</h2>
            {allDecks.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No decks created yet. Generate your first deck above!</p>
            ) : (
              <div className="grid gap-4">
                {allDecks.map((deck) => (
                  <div key={deck.id} className="border border-gray-200 rounded-lg p-4 flex justify-between items-center hover:bg-gray-50">
                    <div className="flex-1 cursor-pointer" onClick={() => selectDeck(deck)}>
                      <h3 className="font-semibold text-gray-800">{deck.name}</h3>
                      <p className="text-sm text-gray-600">{deck.cards.length} cards • {deck.language}</p>
                      <p className="text-xs text-gray-400">Created: {new Date(deck.created_at).toLocaleDateString()}</p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteDeck(deck.id);
                      }}
                      className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
                    >
                      🗑️
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Flash Card Display */}
        {currentDeck && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-semibold text-gray-800 mb-2">{currentDeck.name}</h2>
              <p className="text-gray-600">
                Card {currentCardIndex + 1} of {currentDeck.cards.length}
              </p>
            </div>

            <div className="max-w-2xl mx-auto mb-6">
              <FlashCard 
                card={currentDeck.cards[currentCardIndex]}
                isFlipped={isCardFlipped}
                onFlip={flipCard}
              />
            </div>

            <div className="flex justify-center gap-4">
              <button
                onClick={prevCard}
                disabled={currentCardIndex === 0}
                className="px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 disabled:opacity-50 transition-colors"
              >
                ← Previous
              </button>
              
              <button
                onClick={flipCard}
                className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                🔄 Flip Card
              </button>

              <button
                onClick={nextCard}
                disabled={currentCardIndex === currentDeck.cards.length - 1}
                className="px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 disabled:opacity-50 transition-colors"
              >
                Next →
              </button>
            </div>

            <div className="mt-4 text-center">
              <p className="text-sm text-gray-500">Click on the card to flip it</p>
            </div>
          </div>
        )}

        {/* Export Modal */}
        <ExportModal
          isOpen={showExportModal}
          onClose={() => setShowExportModal(false)}
          decks={allDecks}
          onExport={exportDecks}
        />

        {/* Loading overlay for export */}
        {exporting && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 flex items-center space-x-4">
              <div className="loading-spinner"></div>
              <span className="text-gray-700">Exporting your flash cards...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
