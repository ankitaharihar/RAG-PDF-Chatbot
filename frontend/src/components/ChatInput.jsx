function ChatInput() {
  return (
    <div className="chat-input-container">
      <input
        type="text"
        placeholder="Ask anything about your PDF..."
      />

      <button className="send-btn">
        Send
      </button>
    </div>
  );
}

export default ChatInput;