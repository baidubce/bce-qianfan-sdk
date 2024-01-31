import { multiply } from "../index";

describe("multiply function tests", () => {
    it("should return the product of two positive numbers", () => {
        const result = multiply(5, 7);
        expect(result).toBe(35);
    });

    it("should return the product of two negative numbers", () => {
        const result = multiply(-5, -7);
        expect(result).toBe(35);
    });

    it("should return the product of a positive number and zero", () => {
        const result = multiply(5, 0);
        expect(result).toBe(0);
    });

    it("should return the product of two zero", () => {
        const result = multiply(0, 0);
        expect(result).toBe(0);
    });

    it("should return the product of a positive number and a negative number", () => {
        const result = multiply(-5, 7);
        expect(result).toBe(-35);
    });

    it("should return the product of two large numbers", () => {
        const result = multiply(123456789, 987654321);
        expect(result).toBe(121932631112635269);
    });

    it("should handle numbers with decimal points", () => {
        const result = multiply(0.5, 0.7);
        expect(result).toBe(0.35);
    });
});
