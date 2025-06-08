# routes/fridge_bbox_router.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.responses import PlainTextResponse
from app.db.database import get_db
from app.models.db_tables import DetectedBBox, FridgeImage

router = APIRouter()

#  가장 최신 레시피를 DB에서 가져오고 -> 그 레시피의 재료 목록으로 BBox 필터를 함
# 최신 냉장고 이미지에 대한 bbox 목록을 반환
@router.get("/fridge/bbox", operation_id="get_current_bbox")
def get_current_fridge_bboxes(db: Session = Depends(get_db)):
    # 최신 냉장고 이미지 ID 조회
    latest_image = db.query(FridgeImage).order_by(FridgeImage.captured_at.desc()).first()
    if not latest_image:
        return {"bboxes": []}

    bboxes = (
        db.query(DetectedBBox)
        .filter(DetectedBBox.image_id == latest_image.id)
        .all()
    )
    
    # 좌상단 기준 위치만 있어도 화면상 클릭 가능한 라벨 표시나 툴팁 띄우기에 충분
    results = [
        {
            "name": bbox.name,
            "x": bbox.x1,
            "y": bbox.y1
        }
        for bbox in bboxes
    ]

    return {
        "image_id": latest_image.id,
        "bboxes": results
    }
# bbox 리스트를 받아 draw.io에서 표현 가능한 <mxGraphModel> XML로 변환
def generate_drawio_xml(bboxes: list[dict]) -> str:
    fridge_width = 600
    fridge_height = 400

    # 1. 원래 좌표계에서 최대 범위 계산
    max_x = max(max(b["x1"], b["x2"]) for b in bboxes)
    max_y = max(max(b["y1"], b["y2"]) for b in bboxes)

    x_scale = fridge_width / max_x
    y_scale = fridge_height / max_y

    # 2. XML 구조 생성
    xml = [
        '<mxGraphModel>',
        '  <root>',
        '    <mxCell id="0"/>',
        '    <mxCell id="1" parent="0"/>',
        '    <mxCell id="bg" style="shape=rectangle;fillColor=#f0f0f0;" vertex="1" parent="1">',
       f'       <mxGeometry x="0" y="0" width="{fridge_width}" height="{fridge_height}" as="geometry"/>',
        '    </mxCell>',
    ]
    node_id = 2
    for bbox in bboxes:
        name = bbox["name"]
        x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
        x = min(x1, x2) * x_scale
        y = min(y1, y2) * y_scale
        width = abs(x2 - x1) * x_scale
        height = abs(y2 - y1) * y_scale
        cell = f'''    <mxCell id="{node_id}" value="{name}" style="rounded=1;fillColor=#fff2cc;" vertex="1" parent="1">
      <mxGeometry x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:1f}" as="geometry"/>
    </mxCell>'''
        xml.append(cell)
        node_id += 1
    xml.append('  </root>')
    xml.append('</mxGraphModel>')
    return "\n".join(xml)

# draw.io용 XML 다이어그램 반환
@router.get("/fridge/bbox/xml", response_class=PlainTextResponse, operation_id="get_bbox_diagram_xml")
def get_fridge_diagram_xml(db: Session = Depends(get_db)):
    latest_image = db.query(FridgeImage).order_by(FridgeImage.captured_at.desc()).first()
    if not latest_image:
        return ""

    bboxes = (
        db.query(DetectedBBox)
        .filter(DetectedBBox.image_id == latest_image.id)
        .all()
    )

    bbox_list = [
        {
            "name": b.name,
            "x1": b.x1,
            "y1": b.y1,
            "x2": b.x2,
            "y2": b.y2
        }
        for b in bboxes
    ]
    xml = generate_drawio_xml(bbox_list)
    return f'<diagram name="Fridge" id="fridge">\n{xml}\n</diagram>'

