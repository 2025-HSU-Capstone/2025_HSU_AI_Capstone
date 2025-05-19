//npm start //리팩토링된 전체 레이아웃 구조
import "./App.css";
import React, { useState } from "react";
import RecipeStoryboard from "./components/RecipeStoryboard";
import BBoxViewer from "./components/BBoxViewer";

function App() {
  const [recipe, setRecipe] = useState(null);
  const [bboxData, setBboxData] = useState(null);
  const [userInput, setUserInput] = useState(""); // 🔸 사용자 입력 상태
 

  // 📌 레시피 생성 요청
  const handleGenerate = async () => {
    const res = await fetch("http://localhost:8000/generate_recipe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_input: userInput }), // 🔸 사용자 입력 반영
    });
    const json = await res.json();
    setRecipe(json);
  };

  // 📌 BBox 데이터 요청
  const handleFetchBBoxes = async () => {
    const res = await fetch("http://localhost:8000/recipe/bbox");
    const json = await res.json();
    setBboxData(json);
  };

  return (
    <div className="app-container">
      {/* 상단 헤더 */}
      <header className="app-header">
        <h1>냉장고를 부탁해 🍳</h1>
        <div className="actions">
          <button onClick={handleGenerate}>레시피 생성</button>
          <button onClick={handleFetchBBoxes}>BBox 보기</button>
        </div>
      </header>

      {/* 입력창만 본문 상단에 따로 배치 */}
      <div style={{ marginBottom: "1.5rem" }}>
        <input
          type="text"
          placeholder="예: 단백질 많은 레시피 추천해줘"
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              handleGenerate(); // 🔸 엔터 입력 시 자동 실행
            }
          }}
          className="input-box"
        />
      </div>

      {/* 메인 콘텐츠 영역 */}
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
