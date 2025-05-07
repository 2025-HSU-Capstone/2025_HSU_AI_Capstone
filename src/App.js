//npm start //리팩토링된 전체 레이아웃 구조
import "./App.css";
import React, { useState } from "react";
import RecipeStoryboard from "./components/RecipeStoryboard";
import BBoxViewer from "./components/BBoxViewer";

function App() {
  const [recipe, setRecipe] = useState(null);
  const [bboxData, setBboxData] = useState(null);

  const handleGenerate = async () => {
    const res = await fetch("http://localhost:8000/generate_recipe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_input: "든든한 점심 메뉴 추천해줘" }),
    });
    const json = await res.json();
    setRecipe(json);
  };

  const handleFetchBBoxes = async () => {
    const res = await fetch("http://localhost:8000/recipe/bbox");
    const json = await res.json();
    setBboxData(json);
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>SmartFridge 🍳</h1>
        <div className="actions">
          <button onClick={handleGenerate}>레시피 생성</button>
          <button onClick={handleFetchBBoxes}>BBox 보기</button>
        </div>
      </header>

      <main className="main-content">
        <section className="left-panel">
          <RecipeStoryboard recipe={recipe} />
        </section>
        <section className="right-panel">
          {bboxData && (
            <BBoxViewer
              imageUrl={`http://localhost:8000/images/${bboxData.image_filename}`}
              bboxes={bboxData.bboxes}
            />
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
