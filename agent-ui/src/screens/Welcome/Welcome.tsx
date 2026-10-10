/**
 * Welcome Screen - Écran d'accueil
 * Phase 1: Simple écran avec bouton "Start"
 */

export function Welcome() {
  return (
    <div className="welcome-screen">
      <h1>🤖 GOB Agent</h1>
      <p>Your Intelligent Assistant</p>
      <button onClick={() => console.log('Navigate to agent')}>
        Start
      </button>
    </div>
  );
}
