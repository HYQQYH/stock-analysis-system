import React from 'react';

function App() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-800 mb-4">
          Stock Analysis System
        </h1>
        <p className="text-lg text-gray-600 mb-8">
          A comprehensive platform for AI-powered stock market analysis
        </p>
        <div className="space-y-4">
          <p className="text-gray-500">
            Backend API: <span className="font-mono text-indigo-600">http://localhost:8000</span>
          </p>
          <p className="text-gray-500">
            API Docs: <a href="http://localhost:8000/docs" className="text-indigo-600 hover:underline">Swagger UI</a>
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
