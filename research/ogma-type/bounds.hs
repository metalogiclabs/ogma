-- Research-only numeric model for the exact NASA Ogma Doorstop demonstration.
-- This verifies GHC's Int8 literal behavior, NOT generated Copilot or flight code.
import Control.Monad (unless)
import Data.Int (Int8, Int16)
import System.Exit (exitFailure)

sourceAllows :: Int8 -> Bool
sourceAllows x = toInteger x >= 120 && toInteger x <= 180

typedAllows :: Int8 -> Bool
typedAllows x = x >= (120 :: Int8) && x <= (fromInteger 180 :: Int8)

typeCorrectedAllows :: Int16 -> Bool
typeCorrectedAllows x = x >= 120 && x <= 180

main :: IO ()
main = do
  let xs = map fromInteger [-128 .. 127] :: [Int8]
      sourceAccepted = filter sourceAllows xs
      typedAccepted = filter typedAllows xs
      disagreements = filter (\x -> sourceAllows x /= typedAllows x) xs
      wrapped = (fromInteger 180 :: Int8)
      witness = (120 :: Int8)
      check ok msg = unless ok $ putStrLn ("FAIL: " ++ msg) >> exitFailure
  check (wrapped == -76) "180 must narrow to -76 as Int8"
  check (sourceAccepted == [120 .. 127]) "source interval must accept 120..127"
  check (null typedAccepted) "narrowed interval must accept no Int8 values"
  check (disagreements == [120 .. 127]) "mismatch set must be exact"
  check (sourceAllows witness && not (typedAllows witness)) "boundary witness must separate"
  check (typeCorrectedAllows 120 && typeCorrectedAllows 180) "Int16 positive control"
  putStrLn $ "GHC Int8 180 = " ++ show wrapped
  putStrLn $ "source interval accepts " ++ show (length sourceAccepted) ++ " of 256"
  putStrLn $ "typed interval accepts " ++ show (length typedAccepted) ++ " of 256"
  putStrLn $ "disagreements = " ++ show disagreements
  putStrLn "at temperature 120: source TRUE, Int8-narrowed FALSE; Int16 TRUE"
  putStrLn "PASS: finite GHC numeric-type probe (native Ogma/Copilot not inferred)"
