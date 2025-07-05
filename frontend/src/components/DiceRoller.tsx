import React, { useState } from 'react';
import './DiceRoller.css';

interface DiceRollerProps {
  onRollDice: (notation: string) => void;
}

const DiceRoller: React.FC<DiceRollerProps> = ({ onRollDice }) => {
  const [customDice, setCustomDice] = useState('');
  const [diceResults, setDiceResults] = useState<string[]>([]);

  const standardDice = ['1d20', '1d12', '1d10', '1d8', '1d6', '1d4'];

  const handleDiceRoll = (notation: string) => {
    onRollDice(notation);
    // Add to local results display
    setDiceResults((prev) => [notation, ...prev.slice(0, 4)]);
  };

  const handleCustomRoll = () => {
    if (customDice.trim()) {
      handleDiceRoll(customDice);
      setCustomDice('');
    }
  };

  return (
    <div className="dice-roller">
      <h3>Dice Roller</h3>
      <div className="dice-buttons">
        {standardDice.map((dice) => (
          <button
            key={dice}
            className="dice-btn"
            onClick={() => handleDiceRoll(dice)}
          >
            d{dice.substring(2)}
          </button>
        ))}
      </div>
      <div className="custom-dice">
        <input
          type="text"
          value={customDice}
          onChange={(e) => setCustomDice(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleCustomRoll()}
          placeholder="e.g., 2d6+3"
        />
        <button onClick={handleCustomRoll}>Roll</button>
      </div>
      <div className="dice-results">
        {diceResults.map((result, index) => (
          <div key={index} className="dice-result">
            {result}
          </div>
        ))}
      </div>
    </div>
  );
};

export default DiceRoller;