// src/components/RecipeStoryboard.jsx
import React from "react";
import "./RecipeStoryboard.css"; // 스타일이 있다면 유지

function RecipeStoryboard({ recipe }) {
  if (!recipe) {
    return <div className="storyboard-container">여기에 생성된 레시피가 표시됩니다.</div>;
  }

  return (
    <div className="storyboard-container">
      <h2>{recipe.title}</h2>

      <h3>📋 재료</h3>
      <ul>
        {recipe.ingredients.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>

      <h3>🍳 조리 순서</h3>
      {recipe.steps.map((step, i) => (
        <div key={i} style={{ marginBottom: "1rem" }}>
          <strong>{step.step}단계:</strong> {step.text}
          <br />
          <img
            src={step.image_url}
            alt={`step${step.step}`}
            width="300"
            style={{ marginTop: "0.5rem", borderRadius: "8px" }}
          />
        </div>
      ))}
    </div>
  );
}

export default RecipeStoryboard;
