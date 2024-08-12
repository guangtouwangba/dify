from youtube_transcript_api import YouTubeTranscriptApi
from typing import Any, Union, List, Dict
from nltk.tokenize import sent_tokenize
import nltk

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool

nltk.download('punkt')


def fetch_youtube_subtitle(video_id: str) -> List[Dict[str, Any]]:
    return YouTubeTranscriptApi.get_transcript(video_id)


def segment_subtitles(subtitles: List[Dict[str, Any]], time_threshold: float = 5.0,
                      similarity_threshold: float = 0.3) -> List[List[Dict[str, Any]]]:
    segments = []
    current_segment = []

    for i, subtitle in enumerate(subtitles):
        if not current_segment:
            current_segment.append(subtitle)
            continue

        time_diff = subtitle['start'] - (current_segment[-1]['start'] + current_segment[-1]['duration'])
        content_similarity = calculate_similarity(subtitle['text'], current_segment[-1]['text'])

        if time_diff > time_threshold or content_similarity < similarity_threshold:
            segments.append(current_segment)
            current_segment = [subtitle]
        else:
            current_segment.append(subtitle)

    if current_segment:
        segments.append(current_segment)

    return segments


def calculate_similarity(text1: str, text2: str) -> float:
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    return len(intersection) / len(union) if union else 0


def summarize_segment(segment: List[Dict[str, Any]]) -> str:
    full_text = ' '.join(subtitle['text'] for subtitle in segment)
    sentences = sent_tokenize(full_text)

    if len(sentences) <= 2:
        return full_text
    else:
        return ' '.join(sentences[:2]) + '...'


class YoutubeVideoSummary(BuiltinTool):
    def summarize(self, subtitles: List[Dict[str, Any]]) -> str:
        full_text = ' '.join(subtitle['text'] for subtitle in subtitles)
        return full_text

    def _invoke(self, user_id: str, tool_parameters: dict[str, Any]) -> Union[
        ToolInvokeMessage, list[ToolInvokeMessage]]:
        video_id = tool_parameters.get("video_id", "")
        if not video_id:
            return self.create_text_message("Please input a valid video id")

        segment_summary = tool_parameters.get("segment_summary", False)

        subtitles = fetch_youtube_subtitle(video_id)

        if not segment_summary:
            overall_summary = self.summarize(subtitles)
            return self.create_text_message(f"Overall Summary:\n{overall_summary}")

        segments = segment_subtitles(subtitles)
        overall_summary = self.summarize(subtitles)
        segmented_summaries = []

        for i, segment in enumerate(segments, 1):
            start_time = segment[0]['start']
            end_time = segment[-1]['start'] + segment[-1]['duration']
            summary = summarize_segment(segment)
            segmented_summaries.append(f"Segment {i} ({start_time:.2f}s - {end_time:.2f}s): {summary}")

        result = f"Overall Summary:\n{overall_summary}\n\nSegmented Summaries:\n" + "\n".join(segmented_summaries)
        return self.create_text_message(result)
