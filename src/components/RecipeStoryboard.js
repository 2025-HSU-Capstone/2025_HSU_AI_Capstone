// src/components/RecipeStoryboard.jsx
import React, { useState } from "react";
import "./RecipeStoryboard.css";

function RecipeStoryboard({ recipe }) {
  const [currentStep, setCurrentStep] = useState(0);
  if (!recipe) return null;

  const totalSteps = recipe.steps.length;
  const step = recipe.steps[currentStep];

  const handleNext = () => {
    setCurrentStep((prev) => (prev < totalSteps - 1 ? prev + 1 : prev));
  };

  const handlePrev = () => {
    setCurrentStep((prev) => (prev > 0 ? prev - 1 : prev));
  };

  return (
    <div className="storyboard">
      <h2 className="recipe-title">{recipe.title}</h2>
      <p className="ingredients">
        <strong>재료:</strong> {recipe.ingredients.join(", ")}
      </p>

      <div className="step-viewer">
        <button onClick={handlePrev} disabled={currentStep === 0}>
          ◀
        </button>
        <div className="step-card">
        <img
          src={`http://localhost:8000${step.image_url}?v=${step.step}`}
          alt={`Step ${step.step}`}
          onError={() => console.error("❌ 이미지 로딩 실패:", step.image_url)}
        />
        <p>{`Step ${step.step}`}</p>
        </div>
        <button onClick={handleNext} disabled={currentStep === totalSteps - 1}>
          ▶
        </button>
      </div>
    </div>
  );
}

export default RecipeStoryboard;
