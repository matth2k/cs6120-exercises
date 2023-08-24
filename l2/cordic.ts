function cordic(theta: number): number {
    let cstab0: number = 0.78539816339744828000;
    let cstab1: number = 0.46364760900080609000;
    let cstab2: number = 0.24497866312686414000;
    let cstab3: number = 0.12435499454676144000;
    let cstab4: number = 0.06241880999595735000;
    let cstab5: number = 0.03123983343026827700;
    let cstab6: number = 0.01562372862047683100;
    let cstab7: number = 0.00781234106010111110;
    let gamma: number = 0.0;
    let lsin: number = 0.0;
    let lcos: number = 0.6072529350088812561694;
    let divisor: number = 1.0;
    for (let i = 0n; i < 8n; i = i + 1n) {
        let clockwise: boolean = theta - gamma > 0.0;
        let sine_shifted: number = lsin / divisor;
        let cosine_shifted: number = lcos / divisor;
        divisor = divisor * 2.0;
        if (clockwise) {
            lsin = lsin + cosine_shifted;
            lcos = lcos - sine_shifted;
            if (i == 0n) {
                gamma = gamma + cstab0;
            } else if (i == 1n) {
                gamma = gamma + cstab1;
            } else if (i == 2n) {
                gamma = gamma + cstab2;
            } else if (i == 3n) {
                gamma = gamma + cstab3;
            } else if (i == 4n) {
                gamma = gamma + cstab4;
            } else if (i == 5n) {
                gamma = gamma + cstab5;
            } else if (i == 6n) {
                gamma = gamma + cstab6;
            } else {
                gamma = gamma + cstab7;
            }
        } else {
            lsin = lsin - cosine_shifted;
            lcos = lcos + sine_shifted;
            if (i == 0n) {
                gamma = gamma - cstab0;
            } else if (i == 1n) {
                gamma = gamma - cstab1;
            } else if (i == 2n) {
                gamma = gamma - cstab2;
            } else if (i == 3n) {
                gamma = gamma - cstab3;
            } else if (i == 4n) {
                gamma = gamma - cstab4;
            } else if (i == 5n) {
                gamma = gamma - cstab5;
            } else if (i == 6n) {
                gamma = gamma - cstab6;
            } else {
                gamma = gamma - cstab7;
            }
        }
    }
    return lsin;
}
