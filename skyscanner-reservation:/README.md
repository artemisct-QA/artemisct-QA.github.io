# Skyscanner Reservation Date Web App

A clean, responsive React web application for selecting travel reservation dates, built with Skyscanner's design principles and the `react-calendar` library.

**Project Type:** Front-End Engineering Job Simulation (FORAGE)  
**Status:** ✅ Completed & Tested  
**Live Demo:** [View on localhost:3000](http://localhost:3000)

---

## 📋 Overview

This project simulates real front-end work at Skyscanner by creating a functional date reservation interface. The application demonstrates core React development skills, component integration, and testing practices used by professional development teams.

### Key Features

- **Interactive Calendar Component** - Full month view with date navigation
- **Date Selection** - Users can select and view their chosen date in a readable format
- **Continue Button** - Functional action button for form submission flow
- **Responsive Design** - Works seamlessly on desktop and mobile devices
- **Modern UI** - Gradient background and clean card-based layout inspired by Skyscanner's design system
- **Automated Testing** - Includes test suite to verify component renders correctly

---

## 🛠️ Tech Stack

| Technology | Purpose |
|-----------|---------|
| **React 18** | Component-based UI framework |
| **react-calendar** | Interactive calendar component |
| **CSS3** | Styling with flexbox and gradients |
| **Jest** | Unit testing framework |
| **React Testing Library** | Component testing utilities |

---

## 📁 Project Structure

```
skyscanner-reservation/
├── src/
│   ├── App.js              # Main React component (calendar + button)
│   ├── App.css             # Styling (gradient, layout, interactions)
│   ├── App.test.js         # Automated test suite
│   ├── index.js            # React DOM render
│   └── index.css           # Global styles
├── public/
│   ├── index.html          # HTML entry point
│   └── favicon.ico         # App icon
├── package.json            # Dependencies & scripts
└── node_modules/           # Installed packages
```

---

## 🚀 Getting Started

### Prerequisites
- Node.js v14 or higher
- npm or yarn

### Installation

```bash
# Clone or download the project
cd skyscanner-reservation

# Install dependencies
npm install

# Start development server
npm start
```

The app opens at `http://localhost:3000`

### Running Tests

```bash
# Run test suite
npm test -- --watchAll=false

# Expected output:
# PASS  src/App.test.js
# ✓ renders without crashing
```

---

## 💡 Key Implementation Details

### App.js Component
- **State Management:** Uses `useState` hook to track selected date
- **Event Handling:** Calendar onChange callback updates selected date
- **User Feedback:** Displays formatted date string (e.g., "Sunday, May 10, 2026")
- **Action Handler:** Continue button logs to console and displays alert

### App.css Styling
- **Gradient Background:** Purple gradient (`#667eea` → `#764ba2`)
- **Card Layout:** Centered white container with shadow and rounded corners
- **Calendar Styling:** Custom color scheme with blue active state
- **Interactive Effects:** Hover states, button animations, smooth transitions
- **Responsive:** Media queries for mobile devices (< 480px)

### Testing Strategy
- **Render Test:** Verifies component mounts without errors
- **Mock Handling:** Jest mocks `react-calendar` to isolate component behavior
- **Test Isolation:** Clean separation of concerns for maintainability

---

## 📊 What I Learned

This project reinforced essential front-end development practices:

✅ **Component Composition** - Building reusable, focused React components  
✅ **State Management** - Using hooks to manage dynamic user interactions  
✅ **Event Handling** - Connecting user actions to state updates  
✅ **Responsive Design** - Creating layouts that work across devices  
✅ **Testing Best Practices** - Writing tests that verify functionality without brittleness  
✅ **Styling Techniques** - CSS gradients, flexbox, hover effects, animations  
✅ **Third-Party Integration** - Importing and configuring npm packages  
✅ **Development Workflow** - npm scripts, dev servers, build optimization  

---

## 🎯 Features Implemented

### Core Requirements (Completed ✅)

- [x] "Reservation Date" heading
- [x] Interactive calendar component
- [x] Continue button with click handler
- [x] Date display in readable format
- [x] Responsive layout
- [x] Automated test suite passes

### Design Enhancements

- [x] Gradient background for visual appeal
- [x] Smooth button hover animations
- [x] Custom calendar styling
- [x] Mobile-friendly responsive design
- [x] Accessible color contrast

---

## 🔍 How to Use

1. **View Calendar** - The calendar displays the current month (May 2026)
2. **Select Date** - Click any date to select it (highlighted in blue)
3. **View Selection** - Selected date updates in text below the calendar
4. **Continue** - Click the blue button to confirm selection (shows alert)

---

## 📱 Browser Compatibility

- ✅ Chrome (Latest)
- ✅ Safari (Latest)
- ✅ Firefox (Latest)
- ✅ Edge (Latest)
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

---

## 🧪 Testing

### Manual Testing Checklist

- [x] Calendar renders without errors
- [x] Can select different dates
- [x] Selected date updates display
- [x] Continue button is clickable
- [x] Continue button shows alert with selected date
- [x] Layout is responsive on mobile
- [x] Styling looks professional

### Automated Testing

```bash
npm test -- --watchAll=false
# Result: PASS ✅
```

---

## 📚 Resources Used

- [React Documentation](https://react.dev)
- [react-calendar Package](https://www.npmjs.com/package/react-calendar)
- [MDN CSS Reference](https://developer.mozilla.org/en-US/docs/Web/CSS)
- [Jest Testing Guide](https://jestjs.io/docs/getting-started)
- [Skyscanner Design System](https://backpack.github.io)

---

## 🎓 Skills Demonstrated

**Technical:**
- React Hooks (useState)
- Component lifecycle
- Event handling and state updates
- CSS styling and animations
- Responsive design principles
- Unit testing
- Package management (npm)

**Professional:**
- Following requirements precisely
- Code organization and structure
- Writing clean, readable code
- Testing and debugging
- Documentation
- Working with design systems

---

## 📈 Future Enhancements

If expanded, this project could include:

- Date range selection (start → end date)
- Form validation
- API integration for real flight data
- Different calendar views (week, year)
- Timezone handling
- Accessibility improvements (ARIA labels)
- E2E testing with Cypress or Playwright
- Deployment to Vercel or GitHub Pages

---

## 📄 License

This project was created as part of the Skyscanner Front-End Engineering Job Simulation through FORAGE.

---

## 👩‍💻 About This Project

**Created:** May 2026  
**Completion Status:** ✅ Complete  
**Tests Passing:** ✅ Yes  
**Ready for Production:** ✅ Yes

This project demonstrates proficiency in modern React development, responsive design, testing practices, and professional code organization—skills essential for front-end engineering roles at companies like Skyscanner.

---

**Questions or feedback?** Feel free to reach out!
