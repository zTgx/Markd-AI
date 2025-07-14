import argparse
import os
from typing import Dict, List

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from pypdf import PdfReader

def extract_pdf_annotations(pdf_path: str) -> List[Dict]:
    """
    提取PDF文件中的所有注释
    
    参数:
        pdf_path: PDF文件路径
        
    返回:
        包含所有注释信息的字典列表
    """
    reader = PdfReader(pdf_path)
    annotations = []
    
    for page_num, page in enumerate(reader.pages):
        if "/Annots" in page:
            for annot in page["/Annots"]:
                annot_obj = annot.get_object()

                # 只提取高亮（/Highlight）和文本注释（/Text）
                subtype = annot_obj.get("/Subtype")
                if subtype in ("/Highlight", "/Text"):
                    annotation = {
                        "page": page_num + 1,
                        "type": subtype,
                        "contents": str(annot_obj.get("/Contents", "")), # 确保内容是字符串
                        "author": annot_obj.get("/T", ""),
                        "creation_date": annot_obj.get("/CreationDate", ""),
                        "rect": annot_obj.get("/Rect", [])
                    }
                    annotations.append(annotation)
                    print(f"提取到注释: {annotation}")
    
    return annotations

def stream_annotations_to_markdown(annotations: List[Dict], model_name: str = "gemini-1.5-flash-latest"):
    """
    借助生成式AI模型，将PDF注释列表转换为Markdown格式的总结。
    此函数使用流式传输以逐步生成响应。
    
    参数:
        annotations: 从PDF提取的注释字典列表
        model_name: 要使用的Gemini模型名称
        
    返回:
        一个生成器，逐块产生AI生成的Markdown内容。
    """
    if not annotations:
        yield "未找到任何注释进行处理。"
        return

    # 为AI构建一个清晰的提示
    prompt_parts = [
        "你是一个高效的助手，负责将PDF注释总结为清晰、易读的Markdown格式。",
        "请将以下结构化的注释数据转换为一个Markdown文档。如果一个注释没有内容，请指明。",
        "请按页码对注释进行分组。对于每个注释，请包含其内容和类型（例如高亮、下划线、笔记）。\n",
    ]

    for annot in annotations:
        # 清理数据以便更好地呈现给模型
        content = annot.get('contents', 'N/A').strip()
        annot_type = str(annot.get('type', '/Text')).replace('/', '') # 清理类型名称
        page = annot.get('page', '未知')
        
        prompt_parts.append(f"- 第 {page} 页:")
        prompt_parts.append(f"  - 类型: {annot_type}")
        prompt_parts.append(f"  - 内容: {content}")

    prompt = "\n".join(prompt_parts)

    # 调用AI模型
    model = genai.GenerativeModel(model_name)
    # 使用流式传输以获得更快的初始响应
    response_stream = model.generate_content(prompt, stream=True)
    yield from response_stream

def main():
    parser = argparse.ArgumentParser(description="从PDF文件中提取注释并借助AI总结为Markdown格式。")
    parser.add_argument("pdf_path", type=str, help="Path to the PDF file.")
    parser.add_argument("--api_key", type=str, default=os.environ.get("GOOGLE_API_KEY"), help="你的Google AI API密钥。也可以通过 GOOGLE_API_KEY 环境变量设置。")
    parser.add_argument("--model", type=str, default="gemini-1.5-flash-latest", help="要使用的生成式模型 (例如 gemini-1.5-flash-latest)。")
    
    args = parser.parse_args()
    
    if not args.api_key:
        raise ValueError("必须提供Google AI API密钥。请使用 --api_key 参数或设置 GOOGLE_API_KEY 环境变量。")

    genai.configure(api_key=args.api_key)

    try:
        # 1. 提取注释
        print(f"正在从 '{args.pdf_path}' 提取注释...")
        annotations = extract_pdf_annotations(args.pdf_path)        
        
        if not annotations:
            print(f"在 '{args.pdf_path}' 中未找到任何注释。")
            return

        print(f"找到 {len(annotations)} 条注释。正在使用AI进行总结...")

        # 2. 使用AI流式转换为Markdown并打印
        # markdown_stream = stream_annotations_to_markdown(annotations, model_name=args.model)

        # print("\n--- AI 生成的Markdown总结 ---\n")
        # for chunk in markdown_stream:
        #     print(chunk.text, end="", flush=True)
        # print("\n-------------------------------------\n")

    except FileNotFoundError:
        print(f"错误: 文件 '{args.pdf_path}' 未找到。")
    except google_exceptions.PermissionDenied as e:
        print(f"\nAPI权限错误: {e}")
        print("请检查你的API密钥是否有效并已启用Gemini API。")
    except google_exceptions.BadRequest as e:
        # 捕获特定的地理位置错误
        print(f"\nAPI请求错误: {e}")
        print("这通常意味着你所在的地区不支持此API。请考虑使用VPN连接到支持的地区（如美国）。")
    except Exception as e:
        print(f"发生意外错误: {e}")

if __name__ == "__main__":
    main()
