import React, { useState } from 'react';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';
import './App.css';

function App() {
  const [selectedDate, setSelectedDate] = useState(new Date());

  const handleContinue = () => {
    console.log('Selected date:', selectedDate);
    alert(`You selected: ${selectedDate.toDateString()}`);
  };

  return (
    <div className="App">
      <div className="container">
        <h1>Reservation Date</h1>
        
        <div className="calendar-wrapper">
          <Calendar
            onChange={setSelectedDate}
            value={selectedDate}
            className="custom-calendar"
          />
        </div>

        <p className="selected-date">
          Selected: {selectedDate.toLocaleDateString('en-US', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
          })}
        </p>

        <button 
          onClick={handleContinue}
          className="continue-button"
        >
          Continue
        </button>
      </div>
    </div>
  );
}

export default App;