//npm start //리팩토링된 전체 레이아웃 구조
import "./App.css";
import React, { useState } from "react";
import RecipeStoryboard from "./components/RecipeStoryboard";
import BBoxViewer from "./components/BBoxViewer";
import FridgeSegOverlay from "./components/FridgeSegOverlay";

function App() {
  const [recipe, setRecipe] = useState(null);
  const [bboxData, setBboxData] = useState(null);
  const [userInput, setUserInput] = useState(""); // 🔸 사용자 입력 상태
  

  // 📌 레시피 생성 요청
 const handleGenerate = async () => {
  const modelPayload = {
    user_input: {
      goal: userInput || "든든한 한끼",
      dietary_preference: "매콤한 요리",
      cooking_time: "15분 내외"
    }
  };

  const res = await fetch("http://localhost:8000/generate_recipe/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(modelPayload),
  });

  if (!res.ok) {
    const errorText = await res.text();
    console.error("❌ 요청 실패:", errorText);
    return;
  }

  const json = await res.json();
  console.log("✅ 전체 응답:", json);
  setRecipe(json);
};


  // 📌 BBox 데이터 요청
  const handleFetchBBoxes = async () => {
    const res = await fetch("http://localhost:8000/recipe/bbox");
    const json = await res.json();

    // if (json.error === "레시피가 존재하지 않습니다.") {
    //   alert("❌ 먼저 레시피를 생성해주세요!");
    //   setBboxData(null); // 기존 BBox 제거
    //   return;
    // }

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
              (() => {
                const fullUrl = bboxData.image_filename.startsWith("http")
                  ? bboxData.image_filename
                  : `https://res.cloudinary.com/dawjwfi88/image/upload/smartfridge/captured_images/${bboxData.image_filename.replace(/^\/+/, "")}`;

                return (
                  <BBoxViewer
                    imageUrl={fullUrl}
                    bboxes={bboxData.bboxes}
                  />
                );
              })()
            )}
        </section>
      </main>
     
      

      <section className="seg-panel">
      <h2>🧪 SAM 기반 재료 감지</h2>
      <FridgeSegOverlay 
       userInput={userInput} 
       setUserInput={setUserInput}  />
      </section>

    </div>
  );
}

export default App;
