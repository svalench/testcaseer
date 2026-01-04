"""Screenshot capture and annotation for TestCaseer."""

from pathlib import Path

from PIL import Image, ImageDraw
from playwright.async_api import Page


async def take_screenshot(
    page: Page,
    output_path: Path,
    highlight_selector: str | None = None,
) -> Path:
    """
    Take a screenshot of the page.

    Args:
        page: Playwright Page object
        output_path: Path to save the screenshot
        highlight_selector: CSS selector of element to highlight (optional)

    Returns:
        Path to the saved screenshot
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Take screenshot
    await page.screenshot(path=output_path, full_page=False)

    # Add highlight if selector provided
    if highlight_selector:
        try:
            element = await page.query_selector(highlight_selector)
            if element:
                box = await element.bounding_box()
                if box:
                    # Convert FloatRect to dict
                    box_dict = {
                        "x": box["x"],
                        "y": box["y"],
                        "width": box["width"],
                        "height": box["height"],
                    }
                    add_highlight_box(output_path, box_dict)
        except Exception:
            # If highlighting fails, just return the original screenshot
            pass

    return output_path


def add_highlight_box(image_path: Path, box: dict[str, float]) -> None:
    """
    Add a red highlight box around an element in the screenshot.

    Args:
        image_path: Path to the image file
        box: Bounding box with x, y, width, height
    """
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)

    x = box["x"]
    y = box["y"]
    w = box["width"]
    h = box["height"]

    # Draw red rectangle with 3px border
    for i in range(3):
        draw.rectangle(
            [x - i, y - i, x + w + i, y + h + i],
            outline="red",
        )

    img.save(image_path)


def generate_screenshot_filename(
    step_number: int,
    action_type: str,
    element_id: str | None = None,
) -> str:
    """
    Generate a descriptive filename for a screenshot.

    Args:
        step_number: Step number (1-based)
        action_type: Type of action (click, input, etc.)
        element_id: Optional element identifier

    Returns:
        Filename like "001_click_login-button.png"
    """
    # Sanitize element_id for filename
    if element_id:
        # Remove special characters, keep alphanumeric and hyphens
        safe_id = "".join(c if c.isalnum() or c == "-" else "-" for c in element_id)
        safe_id = safe_id[:30]  # Limit length
        return f"{step_number:03d}_{action_type}_{safe_id}.png"

    return f"{step_number:03d}_{action_type}.png"
