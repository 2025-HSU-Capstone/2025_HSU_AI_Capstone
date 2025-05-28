// src/components/FridgeSegOverlay.js
import React, { useEffect, useRef, useState } from "react";


// tsx는 TypeScript + JSX의 확장자.  타입이 있는 JavaScript. 
// //복잡한 프로젝트에선 에러를 줄이고 코드 품질을 높일 수 있어.
// 즉, React 컴포넌트를 TypeScript로 작성할 때 사용하는 파일 형식이야.
// .tsx 파일은 내부에 <div>...</div> 같은 JSX 문법이 들어갈 수 있는 TypeScript 파일임.
function nameToColor(name) {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue}, 80%, 70%)`; // 파스텔 계열
}


function FridgeSegOverlay() {
  const [baseImageUrl, setBaseImageUrl] = useState("");
  const [masks, setMasks] = useState([]); // { name, image }
  const [hovered, setHovered] = useState(null);
  const [selected, setSelected] = useState(null);
  const canvasRef = useRef(null);
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });


  // ✅ API 요청: 최신 이미지 + 마스크 불러오기
  useEffect(() => {
    fetch("http://localhost:8000/fridge/masks")
      .then((res) => res.json())
      .then(async (data) => {
        console.log("📷 이미지 URL 확인:", data.image_filename);

        setBaseImageUrl(
          data.image_filename.startsWith("http")
            ? data.image_filename
            : `http://localhost:8000/images/${data.image_filename}`
        );

        const loaded = await Promise.all(
          data.masks.map(
            (item) =>
              new Promise((resolve) => {
                const img = new Image();
                img.crossOrigin = "anonymous";
                img.src = encodeURI(item.mask_url);
                img.onload = () => resolve({ name: item.name, image: img });
              })
          )
        );
        setMasks(loaded);
      });
  }, []);

  // ✅ 커서 위치에 알파값 있는 마스크 찾기
  const handleMouseMove = (e) => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    for (let i = 0; i < masks.length; i++) {
      const mask = masks[i];
      ctx.clearRect(0, 0, canvas.width, canvas.height);

       // ✅ 1. 마스크 이미지를 그려놓고 픽셀 조작
      ctx.drawImage(mask.image, 0, 0, canvas.width, canvas.height);

      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imageData.data;

      // ✅ 흰색만 남기고, 나머지는 투명 처리
      for (let j = 0; j < data.length; j += 4) {
        const [r, g, b] = [data[j], data[j + 1], data[j + 2]];
        const isWhite = r > 240 && g > 240 && b > 240;

        if (!isWhite) {
          data[j + 3] = 0; // 완전 투명
        } else {
          // 원하는 색으로 덮을 수도 있음
          data[j] = 255;     // red
          data[j + 1] = 165; // green
          data[j + 2] = 0;   // blue
          data[j + 3] = 120; // alpha (투명도)
        }
      }

      ctx.putImageData(imageData, 0, 0);
      
      // 2. 현재 커서 위치에 알파값 확인
      const pixel = ctx.getImageData(x, y, 1, 1).data;
      if (pixel[3] > 0) {
        // 3. 해당 마스크만 색칠
        ctx.globalCompositeOperation = "source-in";
        ctx.fillStyle = nameToColor(mask.name);
        ctx.globalAlpha = 0.4;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // 4. 상태 업데이트
        ctx.globalAlpha = 1.0;
        ctx.globalCompositeOperation = "source-over";
        setHovered(mask.name);
        return;
      }
    }

    setHovered(null);
  };


  const handleClick = () => {
    if (hovered) {
      setSelected(hovered);
    }
  };

  return (
    <div style={{ 
      position: "relative", 
      width: "1280px", 
      eight: "480px"}}
    >
      <img
        src={baseImageUrl}
        alt="Fridge"
        onLoad={(e) => {
          const img = e.target;
          const width = img.naturalWidth;
          const height = img.naturalHeight;
          setImageSize({ width, height });  // useState로 관리 필요
        }}
        style={{ display: "block" }}
        width={imageSize.width}
        height={imageSize.height}
      />
      <canvas
        ref={canvasRef}
        width={imageSize.width}
        height={imageSize.height}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          pointerEvents: "auto",
        }}
        onMouseMove={handleMouseMove}
        onClick={handleClick}
      />
      <div
        style={{
          position: "absolute",
          bottom: 10,
          left: 10,
          background: "rgba(0,0,0,0.6)",
          color: "white",
          padding: "6px 10px",
          borderRadius: 4,
        }}
      >
        {hovered ? `🖱️ ${hovered} (hover)` : selected ? `✅ ${selected} 선택됨` : "마스크 위에 커서를 올려보세요"}
      </div>
    </div>
  );
}

export default FridgeSegOverlay;
