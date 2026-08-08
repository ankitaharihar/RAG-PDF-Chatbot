import "./App.css";

import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import ChatArea from "./components/ChatArea";
import ChatInput from "./components/ChatInput";
import QuickActions from "./components/QuickActions";

function App() {
  return (
    <div className="app">
      <Sidebar />

      <div className="main">
        <Header />
        <ChatArea />
        <ChatInput />
        <QuickActions/>
      </div>
    </div>
  );
}

export default App;