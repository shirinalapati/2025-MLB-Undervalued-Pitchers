import './AboutPage.css'

export default function AboutPage() {
  return (
    <article className="about-page">
      <h3>Project Overview</h3>
      <p>
        This project identifies undervalued MLB pitchers. First, all the basic and advanced statistics are listed on a
        comprehensive table with lots of filtering options for both starting and relief pitchers. Traditional metrics
        like ERA and wins often misrepresent true pitcher skill. By incorporating advanced metrics such as xERA, FIP,
        SIERA, K-BB%, and contact quality indicators, this model isolates sustainable performance and regression
        candidates.
      </p>

      <h3>2026 Live Season</h3>
      <p>
        The app now includes a <strong>2026 Live Season</strong> view alongside the frozen 2025 full-season benchmark.
        Use the season dropdown in the header to switch between them. Updates run on two schedules because UPS
        depends heavily on advanced metrics that are not available from the MLB box-score API alone.
      </p>

      <h4>Two refresh tiers</h4>
      <ul className="index-weights">
        <li>
          <strong>Counting stats (~every 2 hours)</strong> — IP, ERA, strikeouts, walks, WHIP, wins/losses,
          saves, and holds from the MLB Stats API. These show up quickly on the stats tabs.
        </li>
        <li>
          <strong>UPS / advanced stats (~4× per day)</strong> — xERA, barrel%, hard-hit%, WAR, and the full
          six-index UPS calculation from Statcast and Baseball Reference.{' '}
          <strong>Raw UPS only changes on this schedule.</strong> Most of the UPS formula weight sits here:
          Run Prevention (25%) uses xERA/FIP/SIERA, Salary Efficiency (15%) uses WAR, Stuff Quality (10%) uses
          contact metrics, and Luck Adjustment (15%) uses xERA and BABIP.
        </li>
      </ul>
      <p>
        Between Statcast refreshes, <strong>Reliability %</strong> and <strong>Adj. UPS</strong> can still move
        when IP updates (more innings → higher reliability → Adj. UPS drifts toward Raw UPS), but{' '}
        <strong>Raw UPS itself stays frozen</strong> until the next full Statcast pull. Check both timestamps
        in the header when judging how current a ranking is.
      </p>
      <p>
        Unlike 2025, the 2026 view includes every pitcher with Statcast data and does not require a minimum innings
        threshold. Because early-season samples can be noisy, the leaderboard uses a <strong>reliability-adjusted UPS</strong>{' '}
        that regresses scores toward the league average for pitchers with fewer innings. Rows highlighted in{' '}
        <strong>yellow</strong> flag low sample sizes — treat those pitchers with caution until they accumulate more
        innings.
      </p>

      <h4>2026 leaderboard columns: Raw UPS, Reliability %, and Adj. UPS</h4>
      <p>
        The 2026 UPS Leaderboard shows three related columns. They use the same six-index UPS formula as 2025 — the
        only difference is how much we trust that score based on innings pitched.
      </p>
      <ul className="index-weights">
        <li>
          <strong>Raw UPS</strong> — The standard Undervalued Pitcher Score computed from the six weighted indexes
          (Dominance, Command, Run Prevention, Stuff, Luck Adjustment, Salary Efficiency). This is the same UPS
          calculation used in 2025. A reliever with 10 IP and great rate stats can still show a very high Raw UPS
          even though that score is mostly noise.
        </li>
        <li>
          <strong>Reliability %</strong> — How much weight we give to that pitcher&apos;s Raw UPS based on sample
          size. It is calculated as <strong>IP ÷ (IP + k)</strong>, where <em>k</em> is 40 for starters and 20 for
          relievers. More innings → higher Reliability %. At 40 IP a starter is at 50% reliability; at 80 IP, about
          67%. At 20 IP a reliever is at 50%; at 40 IP, about 67%.
        </li>
        <li>
          <strong>Adj. UPS (Adjusted UPS)</strong> — The score used to rank the 2026 leaderboard. It blends Raw UPS
          with a neutral score of 50 (league-average UPS on the 0–100 scale):{' '}
          <strong>Adj. UPS = (Reliability × Raw UPS) + ((1 − Reliability) × 50)</strong>. A pitcher with low IP
          gets pulled toward 50; a pitcher with lots of IP looks almost identical to their Raw UPS. Example: Raw UPS
          of 80 with 20% reliability → Adj. UPS of 56 (mostly regressed). Same Raw UPS with 80% reliability → Adj.
          UPS of 74 (mostly trusted).
        </li>
      </ul>
      <p>
        <strong>Which column should you use?</strong> For 2026 rankings, use <strong>Adj. UPS</strong>. Check{' '}
        <strong>Raw UPS</strong> to see how extreme the underlying metrics look before sample-size adjustment, and
        check <strong>Reliability %</strong> (and yellow highlighting) to decide how much to trust either number.
      </p>

      <h3>2025 Full Season</h3>
      <p>
        The 2025 view is a completed-season snapshot. Starters needed at least 80 innings pitched and relievers at
        least 30 innings to qualify. Rankings use raw UPS with no reliability adjustment.
      </p>

      <p>
        Using a composite model that blends dominance metrics, expected run prevention, contact quality, luck indicators,
        and salary efficiency. The goal is to surface pitchers whose underlying performance suggests stronger future
        value than traditional statistics or contract size might imply.
      </p>

      <h3>The Formula</h3>
      <p>
        <strong>So, I created a formula that has six separate indexes that have their own formulas to them.</strong>{' '}
        Those are displayed on the &quot;Undervalued Pitchers Score Leaderboard&quot; on the final tab.{' '}
        <strong>
          Each index consists of a collection of both advanced and traditional pitching metrics listed in the
          glossary. However, not all indexes are weighted equally, here are their weights:
        </strong>
      </p>

      <ul className="index-weights">
        <li>
          <strong>Dominance Index (20%)</strong> – Strikeout and K-BB% ability
        </li>
        <li>
          <strong>Command Index (15%)</strong> – Walk rate and control
        </li>
        <li>
          <strong>Run Prevention Skill (25%)</strong> – xERA, FIP, SIERA
        </li>
        <li>
          <strong>Stuff Quality (10%)</strong> – Velocity and contact suppression
        </li>
        <li>
          <strong>Luck Adjustment (15%)</strong> – ERA vs xERA gap, BABIP, LOB%
        </li>
        <li>
          <strong>Salary Efficiency (15%)</strong> – Production relative to Average Annual Value
        </li>
      </ul>

      <h3>Scaling</h3>
      <p>
        For each pitcher&apos;s indices, <strong>raw</strong> values are the outputs of each index&apos;s formula before
        any scaling. They come directly from the pitching stats (K%, BB%, xERA, FIP, SIERA, etc.) and are on different
        scales. For example, Dominance might be ~18 while Run Prevention is ~3.8.
      </p>
      <p>
        <strong>Normalized (0–100)</strong> values are the raw values rescaled so that all indices use a 0–100 range.
        That lets you combine them using fixed weights. Within each index, 100 is best among the pitchers in the sample,
        0 is worst, and values in between show where a pitcher sits relative to the rest.
      </p>
      <p>
        This scaling is what makes the weighted combination (Dominance Index, Command, Run Prevention Skill, etc.) into a
        single UPS score possible, even though the raw indices use different units and scales.
      </p>
      <p>
        Because each index is already normalized onto a common 0–100 scale, differences in unit size and variance have
        been removed, eliminating the need for z-score standardization before weighting. The normalization step ensures
        that each component contributes proportionally to the final UPS without being artificially amplified due to
        scale differences.
      </p>

      <h3>Explanation of Index Weights</h3>
      <p>
        Because the primary goal of this project is to identify undervalued performance — not simply rank pitchers by
        ERA — the Run Prevention Skill Index (25%) is weighted the most heavily. This index consists of expected and
        defense-independent metrics such as xERA, FIP, and SIERA. These statistics isolate underlying pitching skill by
        removing defensive context and sequencing luck, making them more predictive of future performance than ERA.
        Since undervaluation often occurs when surface-level results mask stronger underlying indicators, this component
        drives the model.
      </p>

      <p>
        The Dominance Index (20%) is weighted the second highest. Metrics such as K% and K-BB% are among the strongest
        predictors of sustainable pitcher success. Strikeout and walk differentials reflect a pitcher’s ability to
        control plate appearances independent of fielders or batted-ball variance. Because dominance stabilizes
        relatively quickly and translates well year-over-year, it is prioritized in projecting forward value.
      </p>

      <p>
        The Command &amp; Control Index (15%) follows, measuring walk suppression and zone management. While closely
        related to dominance, command deserves its own weight because limiting free passes significantly reduces
        volatility and enhances sustainability. Strong command profiles are less prone to regression spikes.
      </p>

      <p>
        The Luck Adjustment Index (15%) is weighted equally to command. Since the core aim of the model is identifying
        undervalued arms, indicators such as ERA vs xERA gaps, BABIP deviations, and LOB% anomalies help identify
        pitchers whose results have been suppressed by unfavorable variance. However, it is not weighted higher than
        skill-based indexes because luck alone does not guarantee future performance if the underlying skill indicators
        are weak.
      </p>

      <p>
        The Salary Efficiency Index (15%) is included to quantify market inefficiency. A pitcher providing strong
        underlying performance at a low AAV represents tangible surplus value. However, this index is not dominant
        because undervaluation is first defined by skill misalignment before financial misalignment.
      </p>

      <p>
        Finally, the Stuff Quality Index (10%) is weighted slightly lower than the others. Metrics such as velocity and
        hard contact suppression are important, but they can be partially captured by strikeout and expected run
        prevention metrics. Therefore, this index functions more as a complementary reinforcement rather than a
        primary driver of the model.
      </p>

      <h3>Interpreting the Rankings Example:</h3>
      <ul>
        <li>High UPS = strong underlying skill + regression potential + contract efficiency</li>
        <li>A pitcher with a high UPS but high ERA may be a strong buy-low candidate</li>
        <li>A pitcher with a low UPS but low ERA may be overperforming</li>
      </ul>

      <h3>Summary</h3>
      <p>
        Overall, the weighting structure prioritizes predictive skill indicators first, regression signals second, and
        financial inefficiency third. Along with identifying undervalued players, the idea of diving into all the
        advanced statistics and these indexes was to truly appreciate the greatness of already well-known pitchers. By
        looking at these metrics, it also helps us decide between two extremely elite pitchers when we engage in
        friendly debates with others. All in all, the goal of this webpage was to build an undervalued pitcher score
        that identifies pitchers who combine sustainable dominance, suppressed surface results, and contract value,
        aligning with how modern MLB front offices evaluate buy-low or extension candidates.
      </p>
    </article>
  )
}
