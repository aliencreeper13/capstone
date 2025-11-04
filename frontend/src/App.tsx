import React from 'react';
import './App.css';
import GameBoard from './components/GameBoard';

function App() {
  return (
    <div className="App">
      <GameBoard useMockData={true} pollInterval={2000} />
    </div>
  );
}

export default App;
