import type { ArticleInputPayload } from "../types";

/**
 * Two contrasting synthetic articles (same underlying event) for quick judge demos.
 */
export const DEMO_ARTICLES: ArticleInputPayload[] = [
  {
    source_label: "Reuters wire (neutral)",
    text: `Thousands of demonstrators gathered peacefully near the parliament complex on Saturday, calling for greater transparency in government contracting and stronger anti-corruption safeguards. Organizers said the rally remained non-violent throughout, with volunteers directing crowds and distributing water. Police reported no major incidents and described the event as largely orderly, though several roads were closed for security cordons. Opposition lawmakers who addressed the crowd urged legislative hearings and publication of audit summaries, while coalition supporters emphasized constitutional rights to assembly and petition. City officials said they would review traffic plans for future protests but did not announce policy changes.`,
  },
  {
    source_label: "City tabloid (alarmist)",
    text: `The capital's core was thrown into chaos Saturday as a hostile crowd laid siege to the corridors of power, defying police lines and paralyzing downtown commerce for hours. Authorities condemned what they called an unlawful assembly aimed at intimidating elected leaders, warning that "mob rule" cannot substitute for democratic process. Several arrests were reported after scuffles near barricades; officials alleged that organizers had not fully cooperated with security plans. Business groups said the disruption cost retailers heavily and demanded compensation. Government spokespeople framed the gathering as a coordinated pressure campaign by fringe elements, while offering few details on investigations. Critics of the protest were quoted saying the spectacle undermined stability and normalized confrontation with the state.`,
  },
];
