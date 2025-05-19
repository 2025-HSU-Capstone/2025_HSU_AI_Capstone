// src/components/RecipeStoryboard.jsx
import React from "react";
import "./RecipeStoryboard.css";

function RecipeStoryboard({ recipe }) {
  if (!recipe) return null;

  return (
    <div className="storyboard">
      <h2 className="recipe-title">{recipe.title}</h2>
      <p className="ingredients">
        <strong>재료:</strong> {recipe.ingredients?.join(", ")}
      </p>

      <div className="all-steps">
        {recipe.steps.map((step) => (
          <div key={step.step} className="step-card">
            {step.image_url ? (
              <img
                src={`http://localhost:8000${step.image_url}?v=${step.step}`}
                alt={`Step ${step.step}`}
                onError={() =>
                  console.error("❌ 이미지 로딩 실패:", step.image_url)
                }
              />
            ) : (
              <div className="image-placeholder">이미지 없음</div>
            )}
            <p className="step-number">{`Step ${step.step}`}</p>
            <p className="step-text">{step.text || "설명 없음"}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default RecipeStoryboard;
