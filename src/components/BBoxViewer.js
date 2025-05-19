import React, { useRef, useState, useEffect } from "react";
import "./BBoxViewer.css";

function BBoxViewer({ imageUrl, bboxes }) {
  const imgRef = useRef(null);
  const [scale, setScale] = useState(null);

  const updateScale = () => {
    const img = imgRef.current;
    if (!img) return;

    const naturalW = img.naturalWidth;
    const naturalH = img.naturalHeight;
    const renderedW = img.clientWidth;
    const renderedH = img.clientHeight;

    if (naturalW && naturalH && renderedW && renderedH) {
      setScale({
        x: renderedW / naturalW,
        y: renderedH / naturalH,
      });
    }
  };

  useEffect(() => {
    updateScale(); // 첫 로드 시 실행
    console.log("🧪 imageUrl:", imageUrl); // 컴포넌트 상단 useEffect에 추가

    const resizeObserver = new ResizeObserver(() => {
      updateScale(); //npm 이미지np가 리사이즈되면 scale 갱신
    });

    if (imgRef.current) {
      resizeObserver.observe(imgRef.current);
    }

    return () => resizeObserver.disconnect();
  }, [imageUrl]);

  return (
    <div className="bbox-wrapper">
      <img
        ref={imgRef}
        src={imageUrl}
        alt="Fridge"
        className="bbox-image"
        onLoad={updateScale}
        onError={() => console.warn("❌ 이미지 로딩 실패:", imageUrl)}
        crossOrigin="anonymous"
      />

      {scale &&
        bboxes.map((box, idx) => (
          <div
            key={idx}
            className="bbox-box"
            style={{
              left: box.x1 * scale.x,
              top: box.y1 * scale.y,
              width: (box.x2 - box.x1) * scale.x,
              height: (box.y2 - box.y1) * scale.y,
            }}
          >
            <span className="bbox-label">{box.name}</span>
          </div>
        ))}
    </div>
  );
}

export default BBoxViewer;
