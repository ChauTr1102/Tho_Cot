"""
Asset Studio — turns a campaign brief plus the brand's own product photos into
platform-native, brand-consistent image and video kits.

The studio runs as a node graph rather than a linear pipeline: an inventory step
triages the brand's existing photos, a worksheet assigns every kit slot to REUSE,
REMIX or GENERATE, and image/video/QA/compose nodes execute as soon as their
inputs are ready. A hero image rendered first acts as the style anchor — every
later image passes both the real product photo and the hero as references, which
is what makes a kit look like one photoshoot.

Public entry point: `pipeline.run_studio(plan, campaign_input)`.
"""
