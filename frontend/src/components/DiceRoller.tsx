import React, { useState } from 'react';

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
    <div className="bg-dnd-dark-secondary rounded-lg p-5 shadow-lg">
      <h3 className="text-dnd-gold mb-4 text-lg font-bold">Dice Roller</h3>
      <div className="grid grid-cols-3 gap-2 mb-4">
        {standardDice.map((dice) => (
          <button
            key={dice}
            className="p-2 bg-dnd-player text-dnd-text rounded font-bold transition-all hover:bg-blue-800 hover:-translate-y-0.5 cursor-pointer"
            onClick={() => handleDiceRoll(dice)}
          >
            d{dice.substring(2)}
          </button>
        ))}
      </div>
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={customDice}
          onChange={(e) => setCustomDice(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleCustomRoll()}
          placeholder="e.g., 2d6+3"
          className="flex-1 px-2 py-1.5 bg-dnd-dark-tertiary border border-gray-700 rounded text-dnd-text text-sm"
        />
        <button
          onClick={handleCustomRoll}
          className="p-2 bg-dnd-blue text-white rounded font-bold transition-all hover:bg-blue-600 hover:-translate-y-0.5 cursor-pointer"
        >
          Roll
        </button>
      </div>
      <div className="bg-dnd-dark-tertiary p-3 rounded min-h-[60px] font-mono">
        {diceResults.map((result, index) => (
          <div key={index} className="mb-1 p-1 bg-gray-800 rounded">
            {result}
          </div>
        ))}
      </div>
    </div>
  );
};

export default DiceRoller;
