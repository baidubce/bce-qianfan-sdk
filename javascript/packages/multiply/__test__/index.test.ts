import {multiply} from '../index';
import {expect, describe, it} from 'vitest';

describe('multiply function', () => {
    it('should return the product of two positive numbers', () => {
        const result = multiply(2, 3);
        expect(result).toBe(6);
    });

    it('should return the product of two negative numbers', () => {
        const result = multiply(-2, -3);
        expect(result).toBe(6);
    });

    it('should return the product of a positive and negative number', () => {
        const result = multiply(2, -3);
        expect(result).toBe(-6);
    });

    it('should return the product of two zero', () => {
        const result = multiply(0, 0);
        expect(result).toBe(0);
    });

    it('should return the product of a positive and zero', () => {
        const result = multiply(2, 0);
        expect(result).toBe(0);
    });

    it('should return the product of a zero and positive', () => {
        const result = multiply(0, 2);
        expect(result).toBe(0);
    });
});