"""AI Poster Studio — isolated, additive feature module.

Pipeline: validators -> prompt_builder -> image_generation_service ->
image_processor -> typography -> poster_service (orchestrator) -> ui.

Nothing outside this package is required for the rest of StreamOperiq to
keep working; app.py only calls poster.ui.render() from one page block.
"""
